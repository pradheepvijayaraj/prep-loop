use std::collections::HashSet;

pub(super) fn tokenize(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for character in text.chars() {
        if character.is_alphanumeric() {
            current.extend(character.to_lowercase());
        } else if !current.is_empty() {
            tokens.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

pub(super) fn normalize_phrase(text: &str) -> String {
    tokenize(text).join(" ")
}

pub(super) fn normalize_taxonomy_label(text: &str) -> String {
    tokenize(text)
        .into_iter()
        .filter(|token| token != "and" && token != "the")
        .collect::<Vec<_>>()
        .join(" ")
}

/// Conservative, corpus-stable normalization for search expansion.
///
/// This intentionally handles only suffixes exercised by the bundled corpus;
/// broad linguistic stemming can reorder existing results. The parent search
/// module keeps regression tests for these transformations and typo behavior.
pub(super) fn stem_token(token: &str) -> String {
    if token.chars().all(|character| character.is_ascii_digit()) {
        return token.to_string();
    }
    let character_count = token.chars().count();
    if character_count > 5 && token.ends_with("ies") {
        return format!("{}y", &token[..token.len() - 3]);
    }
    if character_count > 6 && token.ends_with("ing") {
        let mut base = token[..token.len() - 3].to_string();
        collapse_trailing_double(&mut base);
        return base;
    }
    if character_count > 5 && token.ends_with("ed") {
        let mut base = token[..token.len() - 2].to_string();
        collapse_trailing_double(&mut base);
        return base;
    }
    if character_count > 5 && token.ends_with("es") {
        return token[..token.len() - 2].to_string();
    }
    if character_count > 4
        && token.ends_with('s')
        && !token.ends_with("ss")
        && !token.ends_with("is")
        && !token.ends_with("ics")
        && !token.ends_with("us")
    {
        return token[..token.len() - 1].to_string();
    }
    token.to_string()
}

fn collapse_trailing_double(value: &mut String) {
    let mut chars = value.chars().rev();
    let Some(last) = chars.next() else { return };
    if chars.next() == Some(last) {
        value.pop();
    }
}

pub(super) fn ngram_similarity(left: &str, right: &str) -> f64 {
    if left == right {
        return 1.0;
    }
    let size = if left.chars().count().min(right.chars().count()) < 5 {
        2
    } else {
        3
    };
    let left_grams = ngrams(left, size);
    let right_grams = ngrams(right, size);
    if left_grams.is_empty() || right_grams.is_empty() {
        return 0.0;
    }
    let overlap = left_grams.intersection(&right_grams).count() as f64;
    (2.0 * overlap) / (left_grams.len() + right_grams.len()) as f64
}

pub(super) fn is_prefix_variant(left: &str, right: &str) -> bool {
    let left_len = left.chars().count();
    let right_len = right.chars().count();
    let shorter = left_len.min(right_len);
    let longer = left_len.max(right_len);
    shorter >= 4
        && shorter * 5 >= longer * 3
        && (left.starts_with(right) || right.starts_with(left))
}

pub(super) fn is_plausible_typo(left: &str, right: &str) -> bool {
    let left_len = left.chars().count();
    let right_len = right.chars().count();
    let allowed_edits = if left_len.max(right_len) <= 5 { 1 } else { 2 };
    left_len.abs_diff(right_len) <= allowed_edits
        && left.chars().next() == right.chars().next()
        && levenshtein_distance(left, right) <= allowed_edits
}

fn levenshtein_distance(left: &str, right: &str) -> usize {
    let right_chars = right.chars().collect::<Vec<_>>();
    let mut previous = (0..=right_chars.len()).collect::<Vec<_>>();
    let mut current = vec![0; right_chars.len() + 1];
    for (left_index, left_character) in left.chars().enumerate() {
        current[0] = left_index + 1;
        for (right_index, right_character) in right_chars.iter().enumerate() {
            let substitution_cost = usize::from(left_character != *right_character);
            current[right_index + 1] = (current[right_index] + 1)
                .min(previous[right_index + 1] + 1)
                .min(previous[right_index] + substitution_cost);
        }
        std::mem::swap(&mut previous, &mut current);
    }
    previous[right_chars.len()]
}

fn ngrams(value: &str, size: usize) -> HashSet<String> {
    let padded = format!("^{value}$");
    let chars: Vec<char> = padded.chars().collect();
    if chars.len() < size {
        return HashSet::from([padded]);
    }
    chars
        .windows(size)
        .map(|window| window.iter().collect())
        .collect()
}

pub(super) fn is_stop_word(token: &str) -> bool {
    matches!(
        token,
        "a" | "an"
            | "and"
            | "are"
            | "as"
            | "at"
            | "be"
            | "by"
            | "for"
            | "from"
            | "in"
            | "is"
            | "it"
            | "of"
            | "on"
            | "or"
            | "that"
            | "the"
            | "to"
            | "was"
            | "were"
            | "which"
            | "with"
    )
}
