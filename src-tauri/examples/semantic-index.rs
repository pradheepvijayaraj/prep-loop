//! Build the bundled semantic question index entirely in Rust.

use std::cmp::Ordering;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use app_lib::semantic::{
    canonical_question_text, chunk_text, fingerprint, QuantizedVector, SemanticEncoder,
    SemanticIndex, SemanticRecord, EMBEDDING_DIMENSIONS, INDEX_FORMAT_VERSION, MODEL_NAME,
};
use app_lib::taxonomy::{
    main_tags_for_section, retrieval_text, UpscMainTag, UpscSubtag, MAX_SUBTAGS, UPSC_MAIN_TAGS,
};
use serde::{Deserialize, Serialize};

const EMBEDDING_BATCH_SIZE: usize = 64;
const ADDITIONAL_SUBTAG_MINIMUM: f32 = 0.28;
const ADDITIONAL_SUBTAG_MARGIN: f32 = 0.075;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Catalog {
    content_version: u64,
    papers: Vec<CatalogPaper>,
}

#[derive(Debug, Deserialize)]
struct CatalogPaper {
    path: String,
    section: String,
}

#[derive(Debug, Deserialize)]
struct QuestionBank {
    questions: Vec<Question>,
}

#[derive(Debug, Deserialize)]
struct Question {
    id: String,
    question: String,
    #[serde(default)]
    options: Vec<QuestionOption>,
}

#[derive(Debug, Deserialize)]
struct QuestionOption {
    id: String,
    text: String,
}

#[derive(Debug)]
struct PendingQuestion {
    id: String,
    section: String,
    fingerprint: u64,
    chunk_start: usize,
    chunk_count: usize,
}

#[derive(Debug)]
struct SubtagPrototype {
    definition: &'static UpscSubtag,
    embedding: Vec<f32>,
}

#[derive(Debug)]
struct MainTagPrototype {
    definition: &'static UpscMainTag,
    embedding: Vec<f32>,
    subtags: Vec<SubtagPrototype>,
}

#[derive(Debug)]
struct QuestionTags {
    main_tag: String,
    subtags: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct IndexMetadata<'a> {
    format_version: u16,
    model: &'a str,
    dimensions: usize,
    content_version: u64,
    question_count: usize,
    chunk_count: usize,
    taxonomy_vector_count: usize,
    main_tag_counts: BTreeMap<String, usize>,
    section_main_tag_counts: BTreeMap<String, BTreeMap<String, usize>>,
    subtag_counts: BTreeMap<String, usize>,
    byte_count: usize,
}

fn main() -> Result<(), String> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let corpus_root = manifest_dir.join("../static/upsc");
    let output_dir = manifest_dir.join("models/semantic");
    let catalog: Catalog = read_json(&corpus_root.join("catalog.json"))?;

    let mut pending = Vec::new();
    let mut chunks = Vec::new();
    for paper in &catalog.papers {
        let bank: QuestionBank = read_json(&corpus_root.join(&paper.path))?;
        for question in bank.questions {
            let option_refs = question
                .options
                .iter()
                .map(|option| (option.id.as_str(), option.text.as_str()))
                .collect::<Vec<_>>();
            let canonical = canonical_question_text(&question.question, &option_refs);
            let question_chunks = chunk_text(&canonical);
            let chunk_start = chunks.len();
            let chunk_count = question_chunks.len();
            chunks.extend(question_chunks);
            pending.push(PendingQuestion {
                id: question.id,
                section: paper.section.clone(),
                fingerprint: fingerprint(&canonical),
                chunk_start,
                chunk_count,
            });
        }
    }

    println!(
        "Embedding {} chunks for {} questions with {MODEL_NAME}",
        chunks.len(),
        pending.len()
    );
    let mut encoder = SemanticEncoder::new(4)?;
    let embeddings = encoder.embed(chunks, EMBEDDING_BATCH_SIZE)?;
    let prototypes = build_taxonomy_prototypes(&mut encoder)?;
    let classifications = pending
        .iter()
        .map(|question| classify_question(question, &embeddings, &prototypes))
        .collect::<Result<Vec<_>, _>>()?;
    let taxonomy_texts = classifications
        .iter()
        .map(|tags| retrieval_text(&tags.main_tag, &tags.subtags))
        .collect::<Vec<_>>();
    let taxonomy_embeddings = encoder.embed(taxonomy_texts, EMBEDDING_BATCH_SIZE)?;

    let mut records = Vec::with_capacity(pending.len());
    let mut main_tag_counts = BTreeMap::new();
    let mut section_main_tag_counts: BTreeMap<String, BTreeMap<String, usize>> = BTreeMap::new();
    let mut subtag_counts = BTreeMap::new();
    for ((question, tags), taxonomy_embedding) in pending
        .into_iter()
        .zip(classifications)
        .zip(&taxonomy_embeddings)
    {
        let end = question.chunk_start + question.chunk_count;
        let content_vectors = embeddings[question.chunk_start..end]
            .iter()
            .map(|embedding| QuantizedVector::from_embedding(embedding))
            .collect::<Result<Vec<_>, _>>()?;
        *main_tag_counts.entry(tags.main_tag.clone()).or_default() += 1;
        *section_main_tag_counts
            .entry(question.section.clone())
            .or_default()
            .entry(tags.main_tag.clone())
            .or_default() += 1;
        for subtag in &tags.subtags {
            *subtag_counts
                .entry(format!("{} / {subtag}", tags.main_tag))
                .or_default() += 1;
        }
        records.push(SemanticRecord {
            id: question.id,
            fingerprint: question.fingerprint,
            main_tag: tags.main_tag,
            subtags: tags.subtags,
            content_vectors,
            taxonomy_vector: QuantizedVector::from_embedding(taxonomy_embedding)?,
        });
    }

    let question_count = records.len();
    let chunk_count = embeddings.len();
    let bytes = SemanticIndex::from_records(records).to_bytes()?;
    fs::create_dir_all(&output_dir)
        .map_err(|error| format!("Failed to create {}: {error}", output_dir.display()))?;
    let index_path = output_dir.join("questions.semantic.bin");
    fs::write(&index_path, &bytes)
        .map_err(|error| format!("Failed to write {}: {error}", index_path.display()))?;

    let metadata = IndexMetadata {
        format_version: INDEX_FORMAT_VERSION,
        model: MODEL_NAME,
        dimensions: EMBEDDING_DIMENSIONS,
        content_version: catalog.content_version,
        question_count,
        chunk_count,
        taxonomy_vector_count: taxonomy_embeddings.len(),
        main_tag_counts,
        section_main_tag_counts,
        subtag_counts,
        byte_count: bytes.len(),
    };
    let metadata_path = output_dir.join("index.json");
    let metadata_json = serde_json::to_vec_pretty(&metadata)
        .map_err(|error| format!("Failed to serialize semantic metadata: {error}"))?;
    fs::write(&metadata_path, metadata_json)
        .map_err(|error| format!("Failed to write {}: {error}", metadata_path.display()))?;

    println!(
        "Wrote {} questions / {} chunks to {} ({} bytes)",
        question_count,
        chunk_count,
        index_path.display(),
        bytes.len()
    );
    Ok(())
}

fn build_taxonomy_prototypes(
    encoder: &mut SemanticEncoder,
) -> Result<Vec<MainTagPrototype>, String> {
    let main_texts = UPSC_MAIN_TAGS
        .iter()
        .map(|main| {
            format!(
                "UPSC Civil Services syllabus subject: {}. {}",
                main.name, main.description
            )
        })
        .collect::<Vec<_>>();
    let main_embeddings = encoder.embed(main_texts, EMBEDDING_BATCH_SIZE)?;

    let mut subtag_definitions = Vec::new();
    let mut subtag_texts = Vec::new();
    for main in UPSC_MAIN_TAGS {
        for subtag in main.subtags {
            subtag_definitions.push((main.name, subtag));
            subtag_texts.push(format!(
                "UPSC Civil Services topic: {}. Subject: {}. {}",
                subtag.name, main.name, subtag.description
            ));
        }
    }
    let subtag_embeddings = encoder.embed(subtag_texts, EMBEDDING_BATCH_SIZE)?;
    let mut subtag_embeddings = subtag_definitions
        .into_iter()
        .zip(subtag_embeddings)
        .collect::<Vec<_>>();

    UPSC_MAIN_TAGS
        .iter()
        .zip(main_embeddings)
        .map(|(main, embedding)| {
            let subtags = main
                .subtags
                .iter()
                .map(|definition| {
                    let index = subtag_embeddings
                        .iter()
                        .position(|((main_name, subtag), _)| {
                            *main_name == main.name && subtag.name == definition.name
                        })
                        .ok_or_else(|| {
                            format!(
                                "Missing taxonomy prototype: {} / {}",
                                main.name, definition.name
                            )
                        })?;
                    let (_, subtag_embedding) = subtag_embeddings.swap_remove(index);
                    Ok(SubtagPrototype {
                        definition,
                        embedding: subtag_embedding,
                    })
                })
                .collect::<Result<Vec<_>, String>>()?;
            Ok(MainTagPrototype {
                definition: main,
                embedding,
                subtags,
            })
        })
        .collect()
}

fn classify_question(
    question: &PendingQuestion,
    embeddings: &[Vec<f32>],
    prototypes: &[MainTagPrototype],
) -> Result<QuestionTags, String> {
    let end = question.chunk_start + question.chunk_count;
    let question_embeddings = embeddings
        .get(question.chunk_start..end)
        .ok_or_else(|| format!("Missing question embeddings: {}", question.id))?;
    let allowed = main_tags_for_section(&question.section)
        .ok_or_else(|| format!("Unknown taxonomy section: {}", question.section))?;
    let main = prototypes
        .iter()
        .filter(|prototype| {
            allowed
                .iter()
                .any(|candidate| candidate.name == prototype.definition.name)
        })
        .max_by(|left, right| {
            main_tag_similarity(question_embeddings, left)
                .partial_cmp(&main_tag_similarity(question_embeddings, right))
                .unwrap_or(Ordering::Equal)
        })
        .ok_or_else(|| format!("No taxonomy candidate for section: {}", question.section))?;

    let mut ranked_subtags = main
        .subtags
        .iter()
        .map(|prototype| {
            (
                prototype.definition.name,
                document_similarity(question_embeddings, &prototype.embedding),
            )
        })
        .collect::<Vec<_>>();
    ranked_subtags.sort_by(|left, right| right.1.partial_cmp(&left.1).unwrap_or(Ordering::Equal));
    let best_subtag_score = ranked_subtags
        .first()
        .map(|(_, score)| *score)
        .unwrap_or(0.0);
    let subtag_cutoff =
        (best_subtag_score - ADDITIONAL_SUBTAG_MARGIN).max(ADDITIONAL_SUBTAG_MINIMUM);
    let subtags = ranked_subtags
        .into_iter()
        .enumerate()
        .filter(|(index, (_, score))| *index == 0 || *score >= subtag_cutoff)
        .take(MAX_SUBTAGS)
        .map(|(_, (name, _))| name.to_string())
        .collect();

    Ok(QuestionTags {
        main_tag: main.definition.name.to_string(),
        subtags,
    })
}

fn main_tag_similarity(question_embeddings: &[Vec<f32>], prototype: &MainTagPrototype) -> f32 {
    let main_similarity = document_similarity(question_embeddings, &prototype.embedding);
    let best_subtag_similarity = prototype
        .subtags
        .iter()
        .map(|subtag| document_similarity(question_embeddings, &subtag.embedding))
        .fold(f32::NEG_INFINITY, f32::max);
    (0.25 * main_similarity) + (0.75 * best_subtag_similarity)
}

fn document_similarity(document_embeddings: &[Vec<f32>], prototype: &[f32]) -> f32 {
    document_embeddings
        .iter()
        .map(|embedding| cosine_similarity(embedding, prototype))
        .fold(f32::NEG_INFINITY, f32::max)
}

fn cosine_similarity(left: &[f32], right: &[f32]) -> f32 {
    let mut dot_product = 0.0_f32;
    let mut left_norm = 0.0_f32;
    let mut right_norm = 0.0_f32;
    for (left, right) in left.iter().zip(right) {
        dot_product += left * right;
        left_norm += left * left;
        right_norm += right * right;
    }
    if left_norm == 0.0 || right_norm == 0.0 {
        0.0
    } else {
        dot_product / (left_norm.sqrt() * right_norm.sqrt())
    }
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, String> {
    let bytes =
        fs::read(path).map_err(|error| format!("Failed to read {}: {error}", path.display()))?;
    serde_json::from_slice(&bytes)
        .map_err(|error| format!("Failed to parse {}: {error}", path.display()))
}
