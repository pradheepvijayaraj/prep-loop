use super::*;
use std::cmp::Ordering;

pub(super) fn rank_documents(
    documents: &[SearchDocument],
    eligible_indices: &[usize],
    vocabulary: &[String],
    semantic_index: &SemanticIndex,
    query: &str,
    query_embedding: Option<&[f32]>,
    include_fuzzy: bool,
) -> RankingOutcome {
    let tokenized_query = tokenize(query);
    let mut original_tokens = tokenized_query
        .iter()
        .filter(|token| !is_stop_word(token))
        .cloned()
        .collect::<Vec<_>>();
    if original_tokens.is_empty() {
        original_tokens = tokenized_query;
    }
    if original_tokens.is_empty() {
        return RankingOutcome {
            ranked: Vec::new(),
            lexical_matches: 0,
        };
    }

    let token_matches = build_query_token_matches(&original_tokens, vocabulary, include_fuzzy);
    let known_query_tokens = token_matches
        .iter()
        .filter(|query_token| query_token_is_known(query_token))
        .count();
    let query_vocabulary_coverage = known_query_tokens as f64 / original_tokens.len() as f64;
    let query_terms = expanded_query_terms(&original_tokens);
    let query_phrase = normalize_phrase(query);
    let document_count = eligible_indices.len() as f64;
    let mut document_frequencies: HashMap<&str, usize> = HashMap::new();

    for term in query_terms.keys() {
        let count = eligible_indices
            .iter()
            .filter(|index| documents[**index].token_weights.contains_key(term))
            .count();
        document_frequencies.insert(term.as_str(), count);
    }

    let mut lexical_ranked = Vec::new();
    let mut semantic_candidates = Vec::new();

    for index in eligible_indices {
        let document = &documents[*index];
        let (score, matched_query_tokens) = score_lexical_document(
            document,
            &original_tokens,
            &token_matches,
            &query_terms,
            &query_phrase,
            &document_frequencies,
            document_count,
        );

        let semantic_similarities = query_embedding.and_then(|embedding| {
            semantic_index.similarities(
                &document.question_id,
                document.semantic_fingerprint,
                embedding,
            )
        });
        // A free-text phrase must match a meaningful share of its terms in the
        // same document. This prevents unrelated documents that happen to
        // contain one common word from entering through the lexical path,
        // while still allowing semantic retrieval to bridge synonyms.
        let minimum_token_matches = (original_tokens.len() * 3).div_ceil(5);
        if score > LEXICAL_SCORE_MINIMUM && matched_query_tokens >= minimum_token_matches {
            lexical_ranked.push((*index, score));
        }
        if let Some(similarities) = semantic_similarities {
            semantic_candidates.push(SemanticCandidate {
                index: *index,
                content_similarity: f64::from(similarities.content),
                taxonomy_similarity: f64::from(similarities.taxonomy),
            });
        }
    }

    // Candidate admission is based exclusively on the embedded question and
    // its options. Generated taxonomy text is deliberately excluded here: it
    // is broad by design and may only break ties among already-relevant
    // questions. The distribution-aware floor removes the weak cosine tail
    // without relying on a query dictionary or topic-specific rules.
    let semantic_floor = adaptive_semantic_floor(
        &semantic_candidates,
        query_vocabulary_coverage,
        original_tokens.len(),
    );
    let mut semantic_ranked = semantic_candidates
        .into_iter()
        .filter(|candidate| candidate.content_similarity >= semantic_floor)
        .map(|candidate| {
            let taxonomy_support = candidate.taxonomy_similarity.max(0.0);
            (
                candidate.index,
                candidate.content_similarity + taxonomy_support * TAXONOMY_RERANK_WEIGHT,
            )
        })
        .collect::<Vec<_>>();

    let lexical_matches = lexical_ranked.len();
    let ranked = fuse_rankings(documents, &mut lexical_ranked, &mut semantic_ranked);

    RankingOutcome {
        ranked,
        lexical_matches,
    }
}

#[allow(clippy::too_many_arguments)]
fn score_lexical_document(
    document: &SearchDocument,
    original_tokens: &[String],
    token_matches: &[QueryTokenMatch],
    query_terms: &HashMap<String, f64>,
    query_phrase: &str,
    document_frequencies: &HashMap<&str, usize>,
    document_count: f64,
) -> (f64, usize) {
    let mut score = 0.0;
    let mut exact_matches = 0;
    let mut matched_tokens = 0;
    for (term, query_weight) in query_terms {
        let Some(term_frequency) = document.token_weights.get(term) else {
            continue;
        };
        let frequency = *document_frequencies.get(term.as_str()).unwrap_or(&0) as f64;
        let inverse_document_frequency =
            ((document_count - frequency + 0.5) / (frequency + 0.5) + 1.0).ln();
        let saturation =
            (term_frequency * BM25_FREQUENCY_SCALE) / (term_frequency + BM25_SATURATION);
        score += inverse_document_frequency * saturation * query_weight;
    }
    for (index, original) in original_tokens.iter().enumerate() {
        let stem = stem_token(original);
        if document.token_weights.contains_key(original)
            || document.token_weights.contains_key(&stem)
        {
            exact_matches += 1;
            matched_tokens += 1;
        } else if document
            .searchable_tokens
            .iter()
            .any(|token| is_prefix_variant(original, token))
        {
            score += PREFIX_MATCH_BOOST;
            matched_tokens += 1;
        } else if let Some(fuzzy_terms) = token_matches.get(index).map(|item| &item.fuzzy_terms) {
            let best = document
                .searchable_tokens
                .iter()
                .filter_map(|token| fuzzy_terms.get(token).copied())
                .fold(0.0_f64, f64::max);
            if best >= FUZZY_MATCH_MINIMUM {
                score += best.powi(3) * FUZZY_MATCH_WEIGHT;
                matched_tokens += 1;
            }
        }
    }
    if exact_matches > 0 {
        score += TOKEN_COVERAGE_WEIGHT * exact_matches as f64 / original_tokens.len() as f64;
    }
    if original_tokens.len() > 1 && query_phrase.chars().count() >= 2 {
        if document.normalized_question.contains(query_phrase) {
            score += QUESTION_PHRASE_BOOST;
        } else if document.normalized_all.contains(query_phrase) {
            score += ALL_FIELDS_PHRASE_BOOST;
        }
    }
    (score, matched_tokens)
}

fn fuse_rankings(
    documents: &[SearchDocument],
    lexical: &mut [(usize, f64)],
    semantic: &mut [(usize, f64)],
) -> Vec<RankedDocument> {
    let sort = |left: &(usize, f64), right: &(usize, f64)| {
        right
            .1
            .partial_cmp(&left.1)
            .unwrap_or(Ordering::Equal)
            .then_with(|| {
                documents[left.0]
                    .question_id
                    .cmp(&documents[right.0].question_id)
            })
    };
    lexical.sort_by(sort);
    semantic.sort_by(sort);
    let mut scores: HashMap<usize, f64> = HashMap::new();
    for (rank, (index, _)) in lexical.iter().enumerate() {
        *scores.entry(*index).or_default() +=
            LEXICAL_RANK_WEIGHT / (RECIPROCAL_RANK_CONSTANT + rank as f64 + 1.0);
    }
    for (rank, (index, _)) in semantic.iter().enumerate() {
        *scores.entry(*index).or_default() +=
            SEMANTIC_RANK_WEIGHT / (RECIPROCAL_RANK_CONSTANT + rank as f64 + 1.0);
    }
    let best = scores.values().copied().fold(0.0_f64, f64::max);
    let mut ranked = scores
        .into_iter()
        .map(|(index, score)| RankedDocument {
            index,
            score: if best > 0.0 { score / best } else { 0.0 },
        })
        .collect::<Vec<_>>();
    sort_ranked_documents(documents, &mut ranked);
    ranked
}

pub(super) fn sort_ranked_documents(documents: &[SearchDocument], ranked: &mut [RankedDocument]) {
    ranked.sort_by(|left, right| {
        right
            .score
            .partial_cmp(&left.score)
            .unwrap_or(Ordering::Equal)
            .then_with(|| documents[right.index].year.cmp(&documents[left.index].year))
            .then_with(|| {
                documents[left.index]
                    .bank_name
                    .cmp(&documents[right.index].bank_name)
            })
            .then_with(|| {
                documents[left.index]
                    .question_number
                    .cmp(&documents[right.index].question_number)
            })
            .then_with(|| {
                documents[left.index]
                    .question_id
                    .cmp(&documents[right.index].question_id)
            })
    });
}

fn adaptive_semantic_floor(
    candidates: &[SemanticCandidate],
    query_vocabulary_coverage: f64,
    query_token_count: usize,
) -> f64 {
    if candidates.is_empty() {
        return f64::INFINITY;
    }

    let count = candidates.len() as f64;
    let mean = candidates
        .iter()
        .map(|candidate| candidate.content_similarity)
        .sum::<f64>()
        / count;
    let variance = candidates
        .iter()
        .map(|candidate| (candidate.content_similarity - mean).powi(2))
        .sum::<f64>()
        / count;
    let best = candidates
        .iter()
        .map(|candidate| candidate.content_similarity)
        .fold(f64::NEG_INFINITY, f64::max);

    // The closest document must still be plausibly related. Cosine ranking
    // always has a winner, even for random text, so a relative threshold alone
    // would leak arbitrary neighbours. Vocabulary coverage makes the guard a
    // little stricter for long out-of-corpus phrases while preserving genuine
    // one-word semantic queries and typo recovery.
    let confidence_minimum = if query_token_count > 1 && query_vocabulary_coverage < 0.5 {
        SEMANTIC_QUERY_CONFIDENCE_MINIMUM + 0.03
    } else {
        SEMANTIC_QUERY_CONFIDENCE_MINIMUM
    };
    if best < confidence_minimum {
        return f64::INFINITY;
    }

    SEMANTIC_ABSOLUTE_MINIMUM
        .max(mean + variance.sqrt() * SEMANTIC_STANDARD_DEVIATIONS_ABOVE_MEAN)
        .max(best - SEMANTIC_MAXIMUM_DISTANCE_FROM_BEST)
}

fn build_query_token_matches(
    original_tokens: &[String],
    vocabulary: &[String],
    include_fuzzy: bool,
) -> Vec<QueryTokenMatch> {
    original_tokens
        .iter()
        .map(|original| {
            let stem = stem_token(original);
            let exact_known = vocabulary.binary_search(original).is_ok()
                || vocabulary.binary_search(&stem).is_ok();
            let fuzzy_terms = if include_fuzzy && !exact_known && original.chars().count() >= 4 {
                vocabulary
                    .iter()
                    .filter_map(|token| {
                        if !is_plausible_typo(original, token) {
                            return None;
                        }
                        let similarity = ngram_similarity(original, token);
                        (similarity >= 0.58).then_some((token.clone(), similarity))
                    })
                    .collect()
            } else {
                HashMap::new()
            };
            QueryTokenMatch {
                known: exact_known || !fuzzy_terms.is_empty(),
                fuzzy_terms,
            }
        })
        .collect()
}

fn query_token_is_known(query_token: &QueryTokenMatch) -> bool {
    query_token.known
}

fn expanded_query_terms(original_tokens: &[String]) -> HashMap<String, f64> {
    let mut terms = HashMap::new();

    for token in original_tokens {
        let exact_weight = if is_stop_word(token) { 0.2 } else { 1.0 };
        insert_max(&mut terms, token.clone(), exact_weight);

        let stem = stem_token(token);
        if stem != *token {
            insert_max(&mut terms, stem.clone(), exact_weight * 0.88);
        }
    }

    terms
}

fn insert_max(target: &mut HashMap<String, f64>, term: String, weight: f64) {
    let entry = target.entry(term).or_insert(0.0);
    if weight > *entry {
        *entry = weight;
    }
}
