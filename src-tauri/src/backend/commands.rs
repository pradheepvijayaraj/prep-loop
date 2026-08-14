//! Tauri command handlers.
//!
//! Each function is annotated with `#[tauri::command]` and registered in
//! `lib.rs`.  Commands receive a shared `DbState` via Tauri's managed-state
//! mechanism (#13 / #21) instead of opening a fresh connection per call.

use std::collections::HashMap;
use tauri::State;

use super::db;
use super::db::{DbState, SearchIndexState};
use super::scoring;
use super::session;
use super::types::{
    AttemptIdArgs, BankIdArgs, CreateTestAttemptArgs, ImportQuestionBankArgs, ImportResult,
    LoadedSessionPayload, Question, QuestionBankWithQuestions, ResponseState, SaveAnswerArgs,
    SaveSettingsArgs, SearchQuestionsArgs, Settings, StoredQuestionBank, SubmitResult, TestAttempt,
    TestAttemptHistoryEntry, TestResult, ToggleFlagArgs, UpdateTimeArgs,
};
use super::validation;

// ── Helper: acquire the connection from managed state ───────────────────

/// Acquire a lock on the shared database connection.
///
/// Takes `&DbState` (not `&State<DbState>`) to avoid lifetime ambiguity.
/// This works because `State<'_, T>` implements `Deref<Target = T>`, so
/// call sites pass `conn(&db)` and Rust auto-deref-coerces the reference.
///
/// Returns a user-friendly error if the mutex is poisoned (should never
/// happen in practice — panics inside a MutexGuard are the only cause,
/// and we never panic in DB code).
fn conn(db: &DbState) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, String> {
    db.0.lock()
        .map_err(|_| "Failed to acquire database lock".to_string())
}

struct SubmissionContext {
    attempt: TestAttempt,
    questions: Vec<Question>,
    main_tags: HashMap<String, String>,
    analysis: scoring::SubmissionAnalysis,
}

/// Narrow data-access boundary for submission analysis. Command handlers use
/// the SQLite implementation, while scoring orchestration can be unit-tested
/// with an in-memory fake without constructing a database.
trait SubmissionRepository {
    fn attempt(&self, attempt_id: &str) -> Result<Option<TestAttempt>, String>;
    fn questions(&self, bank_id: &str) -> Result<Vec<Question>, String>;
    fn responses(&self, attempt_id: &str) -> Result<Vec<ResponseState>, String>;
    fn main_tags(
        &self,
        search_index: &SearchIndexState,
        questions: &[Question],
    ) -> Result<HashMap<String, String>, String>;
}

impl SubmissionRepository for rusqlite::Connection {
    fn attempt(&self, attempt_id: &str) -> Result<Option<TestAttempt>, String> {
        db::fetch_test_attempt(self, attempt_id)
    }

    fn questions(&self, bank_id: &str) -> Result<Vec<Question>, String> {
        db::fetch_questions_by_bank_id(self, bank_id)
    }

    fn responses(&self, attempt_id: &str) -> Result<Vec<ResponseState>, String> {
        db::fetch_responses_by_attempt_id(self, attempt_id)
    }

    fn main_tags(
        &self,
        search_index: &SearchIndexState,
        questions: &[Question],
    ) -> Result<HashMap<String, String>, String> {
        db::question_main_tags(self, search_index, questions)
    }
}

fn load_submission_context(
    repository: &impl SubmissionRepository,
    search_index: &SearchIndexState,
    attempt_id: &str,
) -> Result<SubmissionContext, String> {
    let Some(attempt) = repository.attempt(attempt_id)? else {
        return Err("Test attempt not found".to_string());
    };
    let questions = repository.questions(&attempt.bank_id)?;
    let responses = repository.responses(attempt_id)?;
    let main_tags = repository.main_tags(search_index, &questions)?;
    let analysis = scoring::analyze_submission(&questions, &responses, &main_tags);
    Ok(SubmissionContext {
        attempt,
        questions,
        main_tags,
        analysis,
    })
}

fn prepend_missing_tags(question: &mut Question, tags: &[String]) {
    for tag in tags.iter().rev() {
        if !question.tags.iter().any(|existing| existing == tag) {
            question.tags.insert(0, tag.clone());
        }
    }
}

// ── Commands ────────────────────────────────────────────────────────────

/// Load the user's persisted settings.
#[tauri::command]
pub fn load_settings(db: State<'_, DbState>) -> Result<Settings, String> {
    let c = conn(&db)?;
    db::load_settings(&c)
}

/// Persist a partial settings patch.
#[tauri::command]
pub fn save_settings(db: State<'_, DbState>, args: SaveSettingsArgs) -> Result<(), String> {
    let mut c = conn(&db)?;
    db::save_settings(&mut c, args.settings)
}

/// Import a question bank from JSON into the database.
///
/// Validates the JSON first; returns validation errors on failure without
/// touching the DB.
#[tauri::command]
pub async fn import_question_bank(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: ImportQuestionBankArgs,
) -> Result<ImportResult, String> {
    let bank = match validation::parse_question_bank_json(&args.json_content) {
        Ok(bank) => bank,
        Err(errors) => {
            return Ok(ImportResult {
                success: false,
                bank_id: None,
                error: Some("Validation failed".to_string()),
                validation_errors: Some(errors),
            })
        }
    };

    let db = db.inner().clone();
    let search_index = search_index.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut c = conn(&db)?;
        let conflicts = db::question_id_conflicts(&c, &bank)?;
        if !conflicts.is_empty() {
            return Ok(ImportResult {
                success: false,
                bank_id: None,
                error: Some("Validation failed".to_string()),
                validation_errors: Some(conflicts),
            });
        }
        let bank_id = match db::import_question_bank(&mut c, &bank) {
            Ok(bank_id) => bank_id,
            Err(error) => {
                log::error!("Question bank import failed: {error}");
                return Ok(ImportResult {
                    success: false,
                    bank_id: None,
                    error: Some("Import failed".to_string()),
                    validation_errors: None,
                });
            }
        };
        // All search paths acquire locks in DB -> cache order, so invalidating
        // before releasing the DB guard closes the stale-read window safely.
        db::invalidate_search_index(&search_index)?;
        Ok(ImportResult {
            success: true,
            bank_id: Some(bank_id),
            error: None,
            validation_errors: None,
        })
    })
    .await
    .map_err(|error| format!("Import task failed: {error}"))?
}

/// List all stored question banks.
#[tauri::command]
pub fn get_question_banks(db: State<'_, DbState>) -> Result<Vec<StoredQuestionBank>, String> {
    let c = conn(&db)?;
    db::fetch_question_banks(&c)
}

/// Fetch a single question bank by ID.
#[tauri::command]
pub fn get_question_bank(
    db: State<'_, DbState>,
    args: BankIdArgs,
) -> Result<Option<StoredQuestionBank>, String> {
    let c = conn(&db)?;
    db::fetch_question_bank(&c, &args.bank_id)
}

/// Fetch a question bank together with its questions.
#[tauri::command]
pub fn get_question_bank_with_questions(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: BankIdArgs,
) -> Result<Option<QuestionBankWithQuestions>, String> {
    let c = conn(&db)?;
    let Some(mut bank) = db::fetch_question_bank_with_questions(&c, &args.bank_id)? else {
        return Ok(None);
    };
    let taxonomy_tags = db::question_taxonomy_tags(&c, &search_index, &bank.questions)?;
    for question in &mut bank.questions {
        if let Some(tags) = taxonomy_tags.get(&question.id) {
            prepend_missing_tags(question, tags);
        }
    }
    Ok(Some(bank))
}

/// Search every stored question and return the strongest semantic-aware hits.
#[tauri::command]
pub async fn search_questions(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: SearchQuestionsArgs,
) -> Result<super::types::QuestionSearchResponse, String> {
    let db = db.inner().clone();
    let search_index = search_index.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let c = conn(&db)?;
        db::search_questions_cached(&c, &search_index, &args.query, args.sections.as_deref())
    })
    .await
    .map_err(|error| format!("Search task failed: {error}"))?
}

/// Delete a question bank (cascading).
#[tauri::command]
pub async fn delete_question_bank(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: BankIdArgs,
) -> Result<(), String> {
    let db = db.inner().clone();
    let search_index = search_index.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut c = conn(&db)?;
        db::delete_question_bank(&mut c, &args.bank_id)?;
        db::invalidate_search_index(&search_index)?;
        Ok(())
    })
    .await
    .map_err(|error| format!("Delete task failed: {error}"))?
}

/// Create a new test attempt.
#[tauri::command]
pub fn create_test_attempt(
    db: State<'_, DbState>,
    args: CreateTestAttemptArgs,
) -> Result<String, String> {
    let mut c = conn(&db)?;
    db::create_test_attempt(&mut c, &args.bank_id, args.mode, args.duration_override)
}

#[tauri::command]
pub fn list_test_attempt_history(
    db: State<'_, DbState>,
) -> Result<Vec<TestAttemptHistoryEntry>, String> {
    let c = conn(&db)?;
    db::list_test_attempt_history(&c)
}

/// Save (or clear) an answer for a question.
#[tauri::command]
pub fn save_answer(db: State<'_, DbState>, args: SaveAnswerArgs) -> Result<(), String> {
    let mut c = conn(&db)?;
    db::save_answer(
        &mut c,
        &args.attempt_id,
        &args.question_id,
        args.answer.as_ref(),
    )
}

/// Toggle the flag on a question.
#[tauri::command]
pub fn toggle_flag(db: State<'_, DbState>, args: ToggleFlagArgs) -> Result<bool, String> {
    let c = conn(&db)?;
    db::toggle_flag(&c, &args.attempt_id, &args.question_id)
}

/// Persist the current timer value.
#[tauri::command]
pub fn update_time_remaining(db: State<'_, DbState>, args: UpdateTimeArgs) -> Result<(), String> {
    let c = conn(&db)?;
    db::update_time_remaining(&c, &args.attempt_id, args.time_remaining)
}

/// Pause a test attempt.
#[tauri::command]
pub fn pause_test(db: State<'_, DbState>, args: UpdateTimeArgs) -> Result<(), String> {
    let c = conn(&db)?;
    db::pause_test(&c, &args.attempt_id, args.time_remaining)
}

/// Resume a paused test attempt.
#[tauri::command]
pub fn resume_test(db: State<'_, DbState>, args: AttemptIdArgs) -> Result<(), String> {
    let c = conn(&db)?;
    db::resume_test(&c, &args.attempt_id)
}

/// Submit a test and compute the score.
///
/// DATA FLOW:
/// 1. Fetch the attempt, its questions, and the user's responses.
/// 2. Run `scoring::analyze_submission` to evaluate each answer.
/// 3. Persist the aggregate score and completion state.
/// 4. Return the score to the frontend for immediate display.
#[tauri::command]
pub fn submit_test(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: AttemptIdArgs,
) -> Result<SubmitResult, String> {
    let c = conn(&db)?;
    let context = load_submission_context(&*c, &search_index, &args.attempt_id)?;
    let completed_at = db::now_ms();

    db::finalize_submission(
        &c,
        &args.attempt_id,
        context.analysis.score,
        context.analysis.max_score,
        completed_at,
    )?;

    Ok(SubmitResult {
        score: context.analysis.score,
        max_score: context.analysis.max_score,
    })
}

/// Fetch a single test attempt.
#[tauri::command]
pub fn get_test_attempt(
    db: State<'_, DbState>,
    args: AttemptIdArgs,
) -> Result<Option<TestAttempt>, String> {
    let c = conn(&db)?;
    db::fetch_test_attempt(&c, &args.attempt_id)
}

/// Calculate the test result for a completed attempt.
#[tauri::command]
pub fn calculate_test_result(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: AttemptIdArgs,
) -> Result<TestResult, String> {
    let c = conn(&db)?;
    let context = load_submission_context(&*c, &search_index, &args.attempt_id)?;
    Ok(scoring::build_test_result(
        &context.attempt,
        &context.analysis,
    ))
}

/// Fetch per-question review data for a completed attempt.
#[tauri::command]
pub fn get_question_review(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: AttemptIdArgs,
) -> Result<Vec<super::types::QuestionReviewItem>, String> {
    let c = conn(&db)?;
    let context = load_submission_context(&*c, &search_index, &args.attempt_id)?;
    Ok(scoring::build_review_items(
        &context.questions,
        &context.analysis,
        &context.main_tags,
    ))
}

/// Load the full session payload for resuming a test attempt.
#[tauri::command]
pub fn get_session_payload(
    db: State<'_, DbState>,
    search_index: State<'_, SearchIndexState>,
    args: AttemptIdArgs,
) -> Result<Option<LoadedSessionPayload>, String> {
    let c = conn(&db)?;
    let Some(attempt) = db::fetch_test_attempt(&c, &args.attempt_id)? else {
        return Ok(None);
    };
    let Some(bank) = db::fetch_question_bank_with_questions(&c, &attempt.bank_id)? else {
        return Err("Question bank not found".to_string());
    };
    let responses = db::fetch_responses_by_attempt_id(&c, &args.attempt_id)?;

    let mut questions = bank.questions;
    let main_tags = db::question_main_tags(&c, &search_index, &questions)?;
    for question in &mut questions {
        if let Some(main_tag) = main_tags.get(&question.id) {
            prepend_missing_tags(question, std::slice::from_ref(main_tag));
        }
    }

    Ok(Some(session::build_loaded_session_payload(
        attempt, questions, responses,
    )))
}
