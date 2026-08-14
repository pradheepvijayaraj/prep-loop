//! Answer evaluation and test result computation.
//!
//! The scoring engine is intentionally stateless: it takes questions +
//! responses and returns evaluation/analysis structs.  The caller
//! (commands.rs) is responsible for persisting the results.
//!
//! SCORING RULES:
//! - Correct answer:   +question.marks
//! - Wrong answer:     -question.negative_marks
//! - Unanswered:       -question.negative_marks_unanswered
//! - Category breakdown uses the same broad UPSC taxonomy as semantic search.

use std::collections::{BTreeMap, HashMap};

use serde_json::Value as JsonValue;

use super::types::{
    CategoryScore, Question, QuestionReviewItem, QuestionType, ResponseState, TestAttempt,
    TestResult,
};

/// Per-question evaluation result produced by `analyze_submission`.
///
/// Kept in memory so result and review views can be derived without storing
/// duplicate correctness data for every response.
#[derive(Debug, Clone)]
pub struct QuestionEvaluation {
    pub question_id: String,
    pub user_answer: Option<JsonValue>,
    pub is_correct: Option<bool>, // None = unanswered
    pub is_flagged: bool,
    pub marks_obtained: f64, // positive for correct, negative for wrong/unanswered
}

/// Aggregated analysis of an entire test submission.
#[derive(Debug, Clone)]
pub struct SubmissionAnalysis {
    pub correct: usize,
    pub wrong: usize,
    pub unanswered: usize,
    pub flagged: usize,
    pub score: f64,     // sum of all marks_obtained (can be negative)
    pub max_score: f64, // sum of all question.marks
    pub category_breakdown: Option<Vec<CategoryScore>>,
    pub evaluations: Vec<QuestionEvaluation>,
}

/// Evaluate every question against the user's responses.
///
/// Builds a `SubmissionAnalysis` containing per-question evaluations,
/// aggregate counts, and an optional category breakdown.
pub fn analyze_submission(
    questions: &[Question],
    responses: &[ResponseState],
    main_tags: &HashMap<String, String>,
) -> SubmissionAnalysis {
    let response_map: HashMap<&str, &ResponseState> = responses
        .iter()
        .map(|response| (response.question_id.as_str(), response))
        .collect();

    let mut evaluations = Vec::with_capacity(questions.len());
    let mut correct = 0;
    let mut wrong = 0;
    let mut unanswered = 0;
    let mut flagged = 0;
    let mut score = 0.0;
    let mut max_score = 0.0;
    let mut category_stats: BTreeMap<String, (f64, f64)> = BTreeMap::new();

    for question in questions {
        max_score += question.marks;
        let response = response_map.get(question.id.as_str()).copied();
        let user_answer = response.and_then(|item| item.answer.clone());
        let is_flagged = response.map(|item| item.is_flagged).unwrap_or(false);

        if is_flagged {
            flagged += 1;
        }

        let (is_correct, marks_obtained) = evaluate_question(question, user_answer.as_ref());
        score += marks_obtained;

        match is_correct {
            Some(true) => correct += 1,
            Some(false) => wrong += 1,
            None => unanswered += 1,
        }

        let category = main_tags
            .get(&question.id)
            .map(|item| item.trim())
            .filter(|item| !item.is_empty())
            .unwrap_or("Other");
        let entry = category_stats.entry(category.to_string()).or_default();

        if marks_obtained >= 0.0 {
            entry.0 += marks_obtained;
        } else {
            entry.1 += marks_obtained.abs();
        }

        evaluations.push(QuestionEvaluation {
            question_id: question.id.clone(),
            user_answer,
            is_correct,
            is_flagged,
            marks_obtained,
        });
    }

    SubmissionAnalysis {
        correct,
        wrong,
        unanswered,
        flagged,
        score,
        max_score,
        category_breakdown: if category_stats.is_empty() {
            None
        } else {
            Some(
                category_stats
                    .into_iter()
                    .map(
                        |(category, (positive_marks, negative_marks))| CategoryScore {
                            category,
                            positive_marks,
                            negative_marks,
                        },
                    )
                    .collect(),
            )
        },
        evaluations,
    }
}

/// Build the test result summary shown on the results page.
///
/// `time_taken` is derived from timestamps if `completed_at` is present,
/// or from `duration - time_remaining` for still-active attempts.
pub fn build_test_result(attempt: &TestAttempt, analysis: &SubmissionAnalysis) -> TestResult {
    let time_taken = match attempt.completed_at {
        Some(completed_at) => ((completed_at - attempt.started_at) / 1000).max(0),
        None => (attempt.duration - attempt.time_remaining).max(0),
    };

    TestResult {
        attempt_id: attempt.id.clone(),
        total_questions: analysis.evaluations.len(),
        correct: analysis.correct,
        wrong: analysis.wrong,
        unanswered: analysis.unanswered,
        flagged: analysis.flagged,
        score: analysis.score,
        max_score: analysis.max_score,
        time_taken,
        category_breakdown: analysis.category_breakdown.clone(),
    }
}

/// Build per-question review items for the review page.
///
/// Each item pairs a question with its evaluation so the UI can display
/// the correct answer, the user's answer, and whether they got it right.
pub fn build_review_items(
    questions: &[Question],
    analysis: &SubmissionAnalysis,
    main_tags: &HashMap<String, String>,
) -> Vec<QuestionReviewItem> {
    let evaluation_map: HashMap<&str, &QuestionEvaluation> = analysis
        .evaluations
        .iter()
        .map(|evaluation| (evaluation.question_id.as_str(), evaluation))
        .collect();

    questions
        .iter()
        .map(|question| {
            let evaluation = evaluation_map.get(question.id.as_str()).copied();
            let mut question = question.clone();
            if let Some(main_tag) = main_tags.get(&question.id) {
                if !question.tags.iter().any(|tag| tag == main_tag) {
                    question.tags.insert(0, main_tag.clone());
                }
            }

            QuestionReviewItem {
                question,
                user_answer: evaluation.and_then(|item| item.user_answer.clone()),
                is_correct: evaluation.and_then(|item| item.is_correct).unwrap_or(false),
                is_flagged: evaluation.map(|item| item.is_flagged).unwrap_or(false),
                marks_obtained: evaluation.map(|item| item.marks_obtained).unwrap_or(0.0),
            }
        })
        .collect()
}

/// Evaluate a single question: returns (is_correct, marks_obtained).
///
/// - `None` for unanswered (applies negative_marks_unanswered penalty).
/// - `Some(true/false)` for answered (applies marks or negative_marks).
fn evaluate_question(question: &Question, user_answer: Option<&JsonValue>) -> (Option<bool>, f64) {
    match user_answer {
        None => (None, -question.negative_marks_unanswered),
        Some(answer) => {
            let is_correct = is_answer_correct(question, answer);
            let marks_obtained = if is_correct {
                question.marks
            } else {
                -question.negative_marks
            };

            (Some(is_correct), marks_obtained)
        }
    }
}

/// Check whether a user answer matches the correct answer(s).
///
/// Dispatches to type-specific comparison logic based on `question_type`.
fn is_answer_correct(question: &Question, answer: &JsonValue) -> bool {
    match question.question_type {
        QuestionType::MultipleChoice => {
            let Some(selected) = as_string_array(answer) else {
                return false;
            };

            // Set-equality check: same length + mutual containment.
            selected.len() == question.correct_answers.len()
                && selected
                    .iter()
                    .all(|value| question.correct_answers.iter().any(|ca| ca == value))
                && question
                    .correct_answers
                    .iter()
                    .all(|value| selected.iter().any(|s| s == value))
        }
        // Tolerance note (#10): numerical answers are compared with a
        // 1e-9 absolute tolerance.  This is sufficient for exam-style
        // integer or low-precision decimal answers.  If sub-nano
        // precision is ever required (unlikely for an exam app), switch
        // to a relative-error comparison or fixed-point representation.
        QuestionType::Numerical => numeric_value(answer)
            .and_then(|left| {
                question
                    .correct_answers
                    .first()
                    .and_then(|expected| expected.parse::<f64>().ok())
                    .map(|right| (left - right).abs() < 1e-9)
            })
            .unwrap_or_else(|| {
                normalized_string(answer)
                    .zip(question.correct_answers.first())
                    .map(|(left, right)| left.trim() == right.trim())
                    .unwrap_or(false)
            }),
        QuestionType::FillBlank => normalized_string(answer)
            .zip(question.correct_answers.first())
            .map(|(left, right)| left.trim().eq_ignore_ascii_case(right.trim()))
            .unwrap_or(false),
        _ => normalized_string(answer)
            .map(|value| question.correct_answers.iter().any(|ca| ca == &value))
            .unwrap_or(false),
    }
}

/// Extract a comparable string representation from a JSON value.
///
/// Returns owned `String` because `Number` and `Bool` variants require
/// allocation.  For `String` values the inner text is cloned (#12).
fn normalized_string(value: &JsonValue) -> Option<String> {
    match value {
        JsonValue::String(text) => Some(text.clone()),
        JsonValue::Number(number) => Some(number.to_string()),
        JsonValue::Bool(value) => Some(value.to_string()),
        _ => None,
    }
}

/// Try to interpret a JSON value as `f64`.
///
/// Accepts both JSON numbers and stringified numbers.
fn numeric_value(value: &JsonValue) -> Option<f64> {
    match value {
        JsonValue::Number(number) => number.as_f64(),
        JsonValue::String(text) => text.trim().parse::<f64>().ok(),
        _ => None,
    }
}

/// Convert a JSON array of primitives into a `Vec<String>`.
///
/// Returns `None` if the value is not an array or if any element cannot
/// be normalised to a string.
fn as_string_array(value: &JsonValue) -> Option<Vec<String>> {
    match value {
        JsonValue::Array(values) => values
            .iter()
            .map(normalized_string)
            .collect::<Option<Vec<String>>>(),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backend::types::{Difficulty, QuestionOption};

    fn question(id: &str) -> Question {
        Question {
            id: id.to_string(),
            question_type: QuestionType::SingleChoice,
            question: "Question?".to_string(),
            options: Some(vec![QuestionOption {
                id: "a".to_string(),
                text: "A".to_string(),
            }]),
            correct_answers: vec!["a".to_string()],
            explanation: String::new(),
            marks: 2.0,
            negative_marks: 0.5,
            negative_marks_unanswered: 0.0,
            time_estimate: None,
            difficulty: Some(Difficulty::Medium),
            tags: Vec::new(),
        }
    }

    #[test]
    fn category_breakdown_separates_positive_and_negative_marks() {
        let questions = vec![question("correct"), question("wrong")];
        let responses = vec![
            ResponseState {
                question_id: "correct".to_string(),
                answer: Some(serde_json::json!("a")),
                is_flagged: false,
            },
            ResponseState {
                question_id: "wrong".to_string(),
                answer: Some(serde_json::json!("b")),
                is_flagged: false,
            },
        ];
        let tags = HashMap::from([
            ("correct".to_string(), "Polity".to_string()),
            ("wrong".to_string(), "Polity".to_string()),
        ]);

        let analysis = analyze_submission(&questions, &responses, &tags);
        let category = &analysis.category_breakdown.unwrap()[0];
        assert_eq!(category.positive_marks, 2.0);
        assert_eq!(category.negative_marks, 0.5);
    }
}
