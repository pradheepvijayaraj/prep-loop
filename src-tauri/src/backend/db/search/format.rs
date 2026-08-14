use serde_json::Value as JsonValue;

pub(super) fn metadata_string(metadata: &JsonValue, key: &str) -> String {
    metadata
        .get(key)
        .and_then(JsonValue::as_str)
        .unwrap_or_default()
        .trim()
        .to_string()
}

pub(super) fn display_stage(raw_stage: &str, section: &str) -> String {
    let combined = format!("{raw_stage} {section}").to_lowercase();
    if combined.contains("prelim") {
        "Prelims".to_string()
    } else if combined.contains("main") {
        "Mains".to_string()
    } else if raw_stage.is_empty() {
        "Question Bank".to_string()
    } else {
        title_case(raw_stage)
    }
}

pub(super) fn display_paper(raw_paper: &str, section: &str) -> String {
    let code = if raw_paper.is_empty() {
        section.rsplit('-').next().unwrap_or_default()
    } else {
        raw_paper
    };
    match code.to_ascii_uppercase().as_str() {
        "GS1" => "GS 1".to_string(),
        "GS2" => "GS 2".to_string(),
        "GS3" => "GS 3".to_string(),
        "GS4" => "GS 4".to_string(),
        "CSAT" => "CSAT".to_string(),
        "ESSAY" => "Essay".to_string(),
        "MATHS1" => "Mathematics I".to_string(),
        "MATHS2" => "Mathematics II".to_string(),
        other if other.is_empty() => "Paper".to_string(),
        other => title_case(other),
    }
}

fn title_case(value: &str) -> String {
    value
        .split(|character: char| character == '-' || character == '_' || character.is_whitespace())
        .filter(|part| !part.is_empty())
        .map(|part| {
            let mut chars = part.chars();
            match chars.next() {
                Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                None => String::new(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}
