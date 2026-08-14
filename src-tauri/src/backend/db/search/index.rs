use super::format::{display_paper, display_stage, metadata_string};
use super::*;
use crate::backend::error::ResultExt;
use serde_json::Value as JsonValue;

pub(super) fn load_documents(
    conn: &Connection,
    semantic: &SemanticIndex,
) -> DbResult<Vec<SearchDocument>> {
    let mut statement = conn
        .prepare(
            "SELECT q.id, q.bank_id, q.question, q.options, q.explanation, q.tags,
                    b.name, b.metadata
             FROM questions q
             JOIN question_banks b ON b.id = q.bank_id
             ORDER BY b.id, q.rowid",
        )
        .stringify_err()?;
    let mut rows = statement.query([]).stringify_err()?;
    let mut documents = Vec::new();
    let mut question_numbers: HashMap<String, i64> = HashMap::new();

    while let Some(row) = rows.next().stringify_err()? {
        let question_id: String = row.get(0).stringify_err()?;
        let bank_id: String = row.get(1).stringify_err()?;
        let question: String = row.get(2).stringify_err()?;
        let options_json: Option<String> = row.get(3).stringify_err()?;
        let explanation: String = row.get(4).stringify_err()?;
        let tags_json: Option<String> = row.get(5).stringify_err()?;
        let bank_name: String = row.get(6).stringify_err()?;
        let metadata_json: String = row.get(7).stringify_err()?;

        let options: Vec<QuestionOption> =
            serde_json::from_str(options_json.as_deref().unwrap_or("[]"))
                .map_err(|error| format!("Failed to parse search options: {error}"))?;
        let tags: Vec<String> = serde_json::from_str(tags_json.as_deref().unwrap_or("[]"))
            .map_err(|error| format!("Failed to parse search tags: {error}"))?;
        let metadata: JsonValue = serde_json::from_str(&metadata_json).unwrap_or(JsonValue::Null);

        let number = question_numbers.entry(bank_id.clone()).or_insert(0);
        *number += 1;

        let year = metadata.get("year").and_then(JsonValue::as_i64);
        let section = metadata_string(&metadata, "section");
        let raw_stage = metadata_string(&metadata, "stage");
        let raw_paper = metadata_string(&metadata, "paper");
        let stage = display_stage(&raw_stage, &section);
        let paper = display_paper(&raw_paper, &section);

        let option_text = options
            .iter()
            .map(|option| option.text.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        let option_refs = options
            .iter()
            .map(|option| (option.id.as_str(), option.text.as_str()))
            .collect::<Vec<_>>();
        let semantic_text = canonical_question_text(&question, &option_refs);
        let semantic_fingerprint = fingerprint(&semantic_text);
        let (main_tag, subtags) = semantic
            .tags(&question_id, semantic_fingerprint)
            .map(|(main_tag, subtags)| (main_tag.to_string(), subtags.to_vec()))
            .unwrap_or_default();
        let source_tag_text = tags.join(" ");
        let subtag_text = subtags.join(" ");
        let metadata_text = format!(
            "{bank_name} {year_text} {stage} {paper} {section}",
            year_text = year.map(|value| value.to_string()).unwrap_or_default()
        );

        let mut token_weights = HashMap::new();
        add_field_tokens(&mut token_weights, &question, 1.0);
        add_field_tokens(&mut token_weights, &option_text, 0.68);
        add_field_tokens(&mut token_weights, &explanation, 0.34);
        add_field_tokens(&mut token_weights, &source_tag_text, 0.55);
        add_field_tokens(&mut token_weights, &main_tag, 1.12);
        add_field_tokens(&mut token_weights, &subtag_text, 1.0);
        add_field_tokens(&mut token_weights, &metadata_text, 0.58);

        let normalized_question = normalize_phrase(&question);
        let normalized_all = normalize_phrase(&format!(
            "{question} {option_text} {explanation} {source_tag_text} {main_tag} {subtag_text} {metadata_text}"
        ));
        let searchable_tokens = token_weights.keys().cloned().collect();

        documents.push(SearchDocument {
            question_id,
            bank_id,
            bank_name,
            question_number: *number,
            question,
            options,
            year,
            stage,
            paper,
            section,
            main_tag,
            subtags,
            token_weights,
            searchable_tokens,
            normalized_question,
            normalized_all,
            semantic_fingerprint,
        });
    }

    Ok(documents)
}

fn add_field_tokens(target: &mut HashMap<String, f64>, text: &str, field_weight: f64) {
    for token in tokenize(text) {
        *target.entry(token.clone()).or_insert(0.0) += field_weight;
        let stem = stem_token(&token);
        if stem != token {
            *target.entry(stem).or_insert(0.0) += field_weight * 0.82;
        }
    }
}
