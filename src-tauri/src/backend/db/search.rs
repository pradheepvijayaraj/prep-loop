//! Offline, similarity-ranked search across every stored question.
//!
//! The corpus is deliberately small (about four thousand UPSC questions), so
//! ranking directly from SQLite keeps the implementation deterministic and
//! avoids a network service or a model download. Relevance combines native
//! MiniLM sentence embeddings with weighted lexical, phrase, prefix, stemming,
//! and typo-tolerant signals.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use rusqlite::Connection;
mod format;
mod index;
mod rank;
mod tokenize;

use self::index::load_documents;
use self::rank::{rank_documents, sort_ranked_documents};
use self::tokenize::{
    is_plausible_typo, is_prefix_variant, is_stop_word, ngram_similarity, normalize_phrase,
    normalize_taxonomy_label, stem_token, tokenize,
};

use super::DbResult;
use crate::backend::types::{
    Question, QuestionOption, QuestionSearchResponse, QuestionSearchResult,
};
use crate::semantic::{canonical_question_text, fingerprint, SemanticEncoder, SemanticIndex};

const MIN_RESULTS_BEFORE_FUZZY: usize = 12;
const SEMANTIC_ABSOLUTE_MINIMUM: f64 = 0.30;
const SEMANTIC_QUERY_CONFIDENCE_MINIMUM: f64 = 0.44;
const SEMANTIC_MAXIMUM_DISTANCE_FROM_BEST: f64 = 0.24;
const SEMANTIC_STANDARD_DEVIATIONS_ABOVE_MEAN: f64 = 1.0;
const TAXONOMY_RERANK_WEIGHT: f64 = 0.08;
const RECIPROCAL_RANK_CONSTANT: f64 = 40.0;
const LEXICAL_RANK_WEIGHT: f64 = 1.08;
const SEMANTIC_RANK_WEIGHT: f64 = 1.0;
const BM25_FREQUENCY_SCALE: f64 = 2.2;
const BM25_SATURATION: f64 = 1.2;
const PREFIX_MATCH_BOOST: f64 = 0.42;
const FUZZY_MATCH_MINIMUM: f64 = 0.58;
const FUZZY_MATCH_WEIGHT: f64 = 0.82;
const TOKEN_COVERAGE_WEIGHT: f64 = 1.15;
const QUESTION_PHRASE_BOOST: f64 = 4.2;
const ALL_FIELDS_PHRASE_BOOST: f64 = 2.1;
const LEXICAL_SCORE_MINIMUM: f64 = 0.22;
const SEMANTIC_INDEX_BYTES: &[u8] =
    include_bytes!("../../../models/semantic/questions.semantic.bin");

#[derive(Debug)]
struct SearchDocument {
    question_id: String,
    bank_id: String,
    bank_name: String,
    question_number: i64,
    question: String,
    options: Vec<QuestionOption>,
    year: Option<i64>,
    stage: String,
    paper: String,
    section: String,
    main_tag: String,
    subtags: Vec<String>,
    token_weights: HashMap<String, f64>,
    searchable_tokens: Vec<String>,
    normalized_question: String,
    normalized_all: String,
    semantic_fingerprint: u64,
}

#[derive(Debug)]
struct SearchIndex {
    documents: Vec<SearchDocument>,
    section_documents: HashMap<String, Vec<usize>>,
    taxonomy_documents: HashMap<String, Vec<usize>>,
    vocabulary: Vec<String>,
    semantic: SemanticIndex,
}

/// Cached, pre-tokenized question corpus shared by every search command.
/// SQLite remains the source of truth; this cache is invalidated whenever a
/// question bank is imported or deleted.
#[derive(Clone, Default)]
pub struct SearchIndexState {
    cached: Arc<Mutex<Option<SearchIndex>>>,
    encoder: Arc<Mutex<Option<SemanticEncoder>>>,
}

#[derive(Debug)]
struct RankedDocument {
    index: usize,
    score: f64,
}

#[derive(Debug)]
struct RankingOutcome {
    ranked: Vec<RankedDocument>,
    lexical_matches: usize,
}

#[derive(Debug)]
struct SemanticCandidate {
    index: usize,
    content_similarity: f64,
    taxonomy_similarity: f64,
}

#[derive(Debug)]
struct QueryTokenMatch {
    known: bool,
    fuzzy_terms: HashMap<String, f64>,
}

#[cfg(test)]
pub fn search_questions(conn: &Connection, query: &str) -> DbResult<QuestionSearchResponse> {
    search_questions_scoped(conn, query, None)
}

#[cfg(test)]
pub fn search_questions_scoped(
    conn: &Connection,
    query: &str,
    sections: Option<&[String]>,
) -> DbResult<QuestionSearchResponse> {
    let index = SearchIndex::load(conn)?;
    Ok(search_with_index(&index, query, sections, None))
}

pub fn search_questions_cached(
    conn: &Connection,
    state: &SearchIndexState,
    query: &str,
    sections: Option<&[String]>,
) -> DbResult<QuestionSearchResponse> {
    let query_embedding = state.query_embedding(query)?;
    with_index(conn, state, |index| {
        search_with_index(index, query, sections, query_embedding.as_deref())
    })
}

pub fn invalidate_search_index(state: &SearchIndexState) -> DbResult<()> {
    let mut cached = state
        .cached
        .lock()
        .map_err(|_| "Failed to acquire search-index lock".to_string())?;
    *cached = None;
    Ok(())
}

/// Return the broad UPSC category used by semantic search for each question.
///
/// Keeping this lookup on the search index makes test summaries and search
/// consume one taxonomy source instead of interpreting the question-bank tags
/// independently.
pub fn question_main_tags(
    conn: &Connection,
    state: &SearchIndexState,
    questions: &[Question],
) -> DbResult<HashMap<String, String>> {
    with_index(conn, state, |index| {
        questions
            .iter()
            .filter_map(|question| {
                index
                    .semantic
                    .tags(&question.id, question_fingerprint(question))
                    .map(|(main_tag, _)| (question.id.clone(), main_tag.to_string()))
            })
            .collect()
    })
}

/// Return the broad taxonomy category and subtags for each question.
pub fn question_taxonomy_tags(
    conn: &Connection,
    state: &SearchIndexState,
    questions: &[Question],
) -> DbResult<HashMap<String, Vec<String>>> {
    with_index(conn, state, |index| {
        questions
            .iter()
            .filter_map(|question| {
                index
                    .semantic
                    .tags(&question.id, question_fingerprint(question))
                    .map(|(main_tag, subtags)| {
                        let mut tags = Vec::with_capacity(subtags.len() + 1);
                        tags.push(main_tag.to_string());
                        tags.extend(subtags.iter().cloned());
                        (question.id.clone(), tags)
                    })
            })
            .collect()
    })
}

fn with_index<T>(
    conn: &Connection,
    state: &SearchIndexState,
    operation: impl FnOnce(&SearchIndex) -> T,
) -> DbResult<T> {
    let mut cached = state
        .cached
        .lock()
        .map_err(|_| "Failed to acquire search-index lock".to_string())?;
    if cached.is_none() {
        *cached = Some(SearchIndex::load(conn)?);
    }
    let index = cached
        .as_ref()
        .ok_or_else(|| "Search index was not initialized".to_string())?;
    Ok(operation(index))
}

fn question_fingerprint(question: &Question) -> u64 {
    let options = question
        .options
        .as_deref()
        .unwrap_or_default()
        .iter()
        .map(|option| (option.id.as_str(), option.text.as_str()))
        .collect::<Vec<_>>();
    fingerprint(&canonical_question_text(&question.question, &options))
}

#[cfg(test)]
pub fn semantic_index_freshness(conn: &Connection) -> DbResult<(usize, usize)> {
    let index = SearchIndex::load(conn)?;
    let fresh = index
        .documents
        .iter()
        .filter(|document| {
            index
                .semantic
                .contains(&document.question_id, document.semantic_fingerprint)
        })
        .count();
    Ok((fresh, index.documents.len()))
}

#[cfg(test)]
pub fn semantic_tag_coverage(conn: &Connection) -> DbResult<(usize, usize)> {
    let index = SearchIndex::load(conn)?;
    let tagged = index
        .documents
        .iter()
        .filter(|document| {
            !document.main_tag.trim().is_empty()
                && !document.subtags.is_empty()
                && document.subtags.len() <= crate::taxonomy::MAX_SUBTAGS
        })
        .count();
    Ok((tagged, index.documents.len()))
}

impl SearchIndex {
    fn load(conn: &Connection) -> DbResult<Self> {
        let semantic = SemanticIndex::from_bytes(SEMANTIC_INDEX_BYTES)?;
        let documents = load_documents(conn, &semantic)?;
        let mut vocabulary: Vec<String> = documents
            .iter()
            .flat_map(|document| document.searchable_tokens.iter().cloned())
            .collect();
        vocabulary.sort_unstable();
        vocabulary.dedup();
        let mut section_documents: HashMap<String, Vec<usize>> = HashMap::new();
        let mut taxonomy_documents: HashMap<String, Vec<usize>> = HashMap::new();
        for (index, document) in documents.iter().enumerate() {
            section_documents
                .entry(document.section.clone())
                .or_default()
                .push(index);

            for label in std::iter::once(document.main_tag.as_str())
                .chain(document.subtags.iter().map(String::as_str))
            {
                let normalized = normalize_taxonomy_label(label);
                if !normalized.is_empty() {
                    taxonomy_documents
                        .entry(normalized)
                        .or_default()
                        .push(index);
                }
            }
        }
        for indices in taxonomy_documents.values_mut() {
            indices.sort_unstable();
            indices.dedup();
        }

        Ok(Self {
            documents,
            section_documents,
            taxonomy_documents,
            vocabulary,
            semantic,
        })
    }

    fn eligible_indices(&self, sections: Option<&[String]>) -> Vec<usize> {
        let Some(sections) = sections.filter(|values| !values.is_empty()) else {
            return (0..self.documents.len()).collect();
        };
        let mut indices = sections
            .iter()
            .filter_map(|section| self.section_documents.get(section))
            .flatten()
            .copied()
            .collect::<Vec<_>>();
        indices.sort_unstable();
        indices.dedup();
        indices
    }

    /// Resolve an exact UPSC taxonomy label without any query-specific alias
    /// table. Labels are derived entirely from the tags stored in the bundled
    /// semantic index, and the result is intersected with the active section
    /// scope before it is returned.
    fn exact_taxonomy_indices(
        &self,
        query: &str,
        eligible_indices: &[usize],
    ) -> Option<Vec<usize>> {
        let normalized = normalize_taxonomy_label(query);
        let tagged_indices = self.taxonomy_documents.get(&normalized)?;

        Some(
            tagged_indices
                .iter()
                .copied()
                .filter(|index| eligible_indices.binary_search(index).is_ok())
                .collect(),
        )
    }
}

impl SearchIndexState {
    fn query_embedding(&self, query: &str) -> DbResult<Option<Vec<f32>>> {
        let mut encoder = self
            .encoder
            .lock()
            .map_err(|_| "Failed to acquire semantic-encoder lock".to_string())?;
        if encoder.is_none() {
            *encoder = Some(SemanticEncoder::new(2)?);
        }
        if query.trim().is_empty() {
            return Ok(None);
        }
        encoder
            .as_mut()
            .ok_or_else(|| "Semantic encoder was not initialized".to_string())?
            .embed_query(query.trim())
            .map(Some)
    }
}

fn search_with_index(
    index: &SearchIndex,
    query: &str,
    sections: Option<&[String]>,
    query_embedding: Option<&[f32]>,
) -> QuestionSearchResponse {
    let query = query.trim();
    let eligible_indices = index.eligible_indices(sections);
    let searched_questions = eligible_indices.len();

    if query.is_empty() {
        return QuestionSearchResponse {
            query: String::new(),
            searched_questions,
            total_matches: 0,
            results: Vec::new(),
        };
    }

    let ranked =
        if let Some(taxonomy_indices) = index.exact_taxonomy_indices(query, &eligible_indices) {
            // An exact main-tag or subtag query is a filter, not a fuzzy hint.
            // Every matching question is returned and all are equally relevant;
            // deterministic metadata ordering keeps the complete set browsable.
            let mut ranked = taxonomy_indices
                .into_iter()
                .map(|index| RankedDocument { index, score: 1.0 })
                .collect::<Vec<_>>();
            sort_ranked_documents(&index.documents, &mut ranked);
            ranked
        } else {
            // Exact, semantic, prefix, and phrase ranking is enough for nearly
            // every free-text query. Typo scoring is the expensive fallback and
            // only runs when the fast pass returns a small result set.
            let mut ranking = rank_documents(
                &index.documents,
                &eligible_indices,
                &index.vocabulary,
                &index.semantic,
                query,
                query_embedding,
                false,
            );
            if ranking.lexical_matches < MIN_RESULTS_BEFORE_FUZZY {
                ranking = rank_documents(
                    &index.documents,
                    &eligible_indices,
                    &index.vocabulary,
                    &index.semantic,
                    query,
                    query_embedding,
                    true,
                );
            }
            ranking.ranked
        };

    let total_matches = ranked.len();

    let results = ranked
        .into_iter()
        .map(|ranked| {
            let document = &index.documents[ranked.index];

            QuestionSearchResult {
                question_id: document.question_id.clone(),
                bank_id: document.bank_id.clone(),
                bank_name: document.bank_name.clone(),
                question_number: document.question_number,
                question: document.question.clone(),
                options: document.options.clone(),
                year: document.year,
                stage: document.stage.clone(),
                paper: document.paper.clone(),
                section: document.section.clone(),
                main_tag: document.main_tag.clone(),
                subtags: document.subtags.clone(),
                similarity: ranked.score,
            }
        })
        .collect();

    QuestionSearchResponse {
        query: query.to_string(),
        searched_questions,
        total_matches,
        results,
    }
}

#[cfg(test)]
mod tests {
    use super::{is_plausible_typo, is_prefix_variant, ngram_similarity, stem_token, tokenize};

    #[test]
    fn tokenization_and_stemming_are_predictable() {
        assert_eq!(
            tokenize("Climate-change, 2024"),
            ["climate", "change", "2024"]
        );
        assert_eq!(stem_token("policies"), "policy");
        assert_eq!(stem_token("running"), "run");
        assert_eq!(stem_token("ethics"), "ethics");
    }

    #[test]
    fn ngrams_tolerate_a_small_typo() {
        assert!(ngram_similarity("parliment", "parliament") > 0.6);
        assert!(ngram_similarity("parliment", "geography") < 0.2);
        assert!(is_plausible_typo("parliment", "parliament"));
        assert!(!is_plausible_typo("sourdough", "south"));
    }

    #[test]
    fn prefix_variants_reject_short_or_distant_tokens() {
        assert!(is_prefix_variant("constitutional", "constitution"));
        assert!(is_prefix_variant("govern", "governance"));
        assert!(!is_prefix_variant("sourdough", "s"));
        assert!(!is_prefix_variant("river", "r"));
        assert!(!is_prefix_variant("river", "driver"));
    }
}
