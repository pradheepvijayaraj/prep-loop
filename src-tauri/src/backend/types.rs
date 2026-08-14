//! Shared data types used across the backend.
//!
//! CONVENTIONS:
//! - All structs use `#[serde(rename_all = "camelCase")]` so that field
//!   names match the JavaScript/TypeScript frontend conventions.
//! - Enums stored in SQLite use `as_str()` / `TryFrom<&str>` for
//!   round-tripping.  Serde serialisation uses `kebab-case` or
//!   `lowercase` depending on the JSON schema.
//! - Command argument structs (suffixed with `Args`) only derive
//!   `Deserialize` because they're only read from the frontend.
//! - Domain structs derive both `Serialize` and `Deserialize` because
//!   they may be returned to the frontend or stored in the DB.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;

// ── Enums ───────────────────────────────────────────────────────────────

macro_rules! string_enum {
    (
        $(#[$meta:meta])*
        pub enum $name:ident {
            $($variant:ident => $value:literal),+ $(,)?
        }
        error = $error:literal
    ) => {
        #[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
        $(#[$meta])*
        pub enum $name { $($variant),+ }

        impl $name {
            pub fn as_str(&self) -> &'static str {
                match self { $(Self::$variant => $value),+ }
            }
        }

        impl TryFrom<&str> for $name {
            type Error = String;

            fn try_from(value: &str) -> Result<Self, Self::Error> {
                match value {
                    $($value => Ok(Self::$variant)),+,
                    _ => Err(format!(concat!($error, ": {}"), value)),
                }
            }
        }
    };
}

// The type of a question determines answer evaluation and UI rendering.
string_enum! {
    #[serde(rename_all = "kebab-case")]
    pub enum QuestionType {
        SingleChoice => "single-choice",
        MultipleChoice => "multiple-choice",
        TrueFalse => "true-false",
        FillBlank => "fill-blank",
        Numerical => "numerical",
    }
    error = "Unsupported question type"
}

string_enum! {
    #[serde(rename_all = "lowercase")]
    pub enum Difficulty {
        Easy => "easy",
        Medium => "medium",
        Hard => "hard",
    }
    error = "Unsupported difficulty"
}

// Test is timed; Practice is untimed.
string_enum! {
    #[serde(rename_all = "lowercase")]
    pub enum TestMode {
        Test => "test",
        Practice => "practice",
    }
    error = "Unsupported test mode"
}

// State machine: InProgress -> Paused -> InProgress -> Completed.
string_enum! {
    #[serde(rename_all = "snake_case")]
    pub enum TestStatus {
        InProgress => "in_progress",
        Paused => "paused",
        Completed => "completed",
    }
    error = "Unsupported test status"
}

// ── Domain models ───────────────────────────────────────────────────────

/// A single answer option for choice-based questions.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionOption {
    pub id: String,
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Question {
    pub id: String,
    #[serde(rename = "type")]
    pub question_type: QuestionType,
    pub question: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub options: Option<Vec<QuestionOption>>,
    pub correct_answers: Vec<String>,
    #[serde(default)]
    pub explanation: String,
    pub marks: f64,
    pub negative_marks: f64,
    #[serde(default)]
    pub negative_marks_unanswered: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub time_estimate: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub difficulty: Option<Difficulty>,
    #[serde(default)]
    pub tags: Vec<String>,
}

/// Metadata header of a question bank JSON file.
///
/// The `extra` field captures any unknown keys via `#[serde(flatten)]`
/// so that future schema additions don't require struct changes.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionBankMetadata {
    pub name: String,
    pub exam: String,
    pub total_questions: i64,
    pub difficulty: Difficulty,
    pub default_duration: i64, // seconds
    #[serde(flatten, default)]
    pub extra: BTreeMap<String, JsonValue>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionBank {
    pub metadata: QuestionBankMetadata,
    pub questions: Vec<Question>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StoredQuestionBank {
    pub id: String,
    pub name: String,
    pub exam: String,
    pub metadata: String,
    pub total_questions: i64,
    pub difficulty: Difficulty,
    pub default_duration: i64,
    pub imported_at: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionBankWithQuestions {
    pub id: String,
    pub name: String,
    pub exam: String,
    pub metadata: String,
    pub total_questions: i64,
    pub difficulty: Difficulty,
    pub default_duration: i64,
    pub imported_at: i64,
    pub questions: Vec<Question>,
}

/// A test attempt: one user's session against a question bank.
///
/// Timestamps (`started_at`, `completed_at`) are milliseconds since
/// UNIX epoch.  `time_remaining` is seconds.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TestAttempt {
    pub id: String,
    pub bank_id: String,
    pub mode: TestMode,
    pub status: TestStatus,
    pub duration: i64,             // total configured duration (seconds)
    pub time_remaining: i64,       // seconds left (only meaningful in Test mode)
    pub started_at: i64,           // epoch ms
    pub completed_at: Option<i64>, // epoch ms; None until submission
    pub score: Option<f64>,
    pub max_score: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TestAttemptHistoryEntry {
    pub id: String,
    pub completed_at: i64,
    pub paper: String,
    pub score: f64,
    pub max_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseState {
    pub question_id: String,
    pub answer: Option<JsonValue>,
    pub is_flagged: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CategoryScore {
    pub category: String,
    pub positive_marks: f64,
    pub negative_marks: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TestResult {
    pub attempt_id: String,
    pub total_questions: usize,
    pub correct: usize,
    pub wrong: usize,
    pub unanswered: usize,
    pub flagged: usize,
    pub score: f64,
    pub max_score: f64,
    pub time_taken: i64,
    pub category_breakdown: Option<Vec<CategoryScore>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionReviewItem {
    pub question: Question,
    pub user_answer: Option<JsonValue>,
    pub is_correct: bool,
    pub is_flagged: bool,
    pub marks_obtained: f64,
}

/// One similarity-ranked hit returned by the global question search.
///
/// Correct answers and explanations are intentionally omitted: search is an
/// archive discovery surface, not an answer-key leak. Multiple-choice options
/// are included for compact display alongside the question.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionSearchResult {
    pub question_id: String,
    pub bank_id: String,
    pub bank_name: String,
    pub question_number: i64,
    pub question: String,
    pub options: Vec<QuestionOption>,
    pub year: Option<i64>,
    pub stage: String,
    pub paper: String,
    pub section: String,
    pub main_tag: String,
    pub subtags: Vec<String>,
    /// Normalised relevance in the inclusive range 0.0..=1.0.
    pub similarity: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct QuestionSearchResponse {
    pub query: String,
    pub searched_questions: usize,
    pub total_matches: usize,
    pub results: Vec<QuestionSearchResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Settings {
    pub theme: String,
    pub navigator_expanded: bool,
    pub last_library_selection_id: Option<String>,
    pub practice_show_immediate_feedback: bool,
    pub auto_submit_on_timer_end: bool,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            theme: "system".to_string(),
            navigator_expanded: false,
            last_library_selection_id: None,
            practice_show_immediate_feedback: true,
            auto_submit_on_timer_end: true,
        }
    }
}

/// Partial update payload for settings.
///
/// Only fields that are `Some(...)` are written to the database;
/// `None` fields are left unchanged.  This avoids clobbering settings
/// that the calling UI didn't intend to modify.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct SettingsPatch {
    pub theme: Option<String>,
    pub navigator_expanded: Option<bool>,
    pub last_library_selection_id: Option<String>,
    pub practice_show_immediate_feedback: Option<bool>,
    pub auto_submit_on_timer_end: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImportResult {
    pub success: bool,
    pub bank_id: Option<String>,
    pub error: Option<String>,
    pub validation_errors: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SubmitResult {
    pub score: f64,
    pub max_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AnswerEntry {
    pub question_id: String,
    pub answer: JsonValue,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LoadedSessionPayload {
    pub attempt: TestAttempt,
    pub questions: Vec<Question>,
    pub answers: Vec<AnswerEntry>,
    pub flags: Vec<String>,
}

// ── Command argument structs ────────────────────────────────────────────
//
// These are Deserialize-only wrappers for the arguments passed from the
// Svelte frontend via `invoke("command_name", { args })`.  Tauri
// automatically deserialises the JS object into these structs.

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImportQuestionBankArgs {
    pub json_content: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BankIdArgs {
    pub bank_id: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SearchQuestionsArgs {
    pub query: String,
    pub sections: Option<Vec<String>>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AttemptIdArgs {
    pub attempt_id: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SaveSettingsArgs {
    pub settings: SettingsPatch,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTestAttemptArgs {
    pub bank_id: String,
    pub mode: TestMode,
    pub duration_override: Option<i64>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SaveAnswerArgs {
    pub attempt_id: String,
    pub question_id: String,
    pub answer: Option<JsonValue>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToggleFlagArgs {
    pub attempt_id: String,
    pub question_id: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateTimeArgs {
    pub attempt_id: String,
    pub time_remaining: i64,
}
