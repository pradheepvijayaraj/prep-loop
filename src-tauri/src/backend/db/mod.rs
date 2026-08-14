//! Database access layer.
//!
//! Split into sub-modules by domain (#19):
//! - `schema`   – table creation and versioned migrations
//! - `question_bank` – question bank + question CRUD
//! - `attempt`  – test attempt, responses, flag/save/submit
//! - `settings` – user settings CRUD
//! - `helpers`  – shared utilities (parsing, time, schema inspection)

// Sub-modules are `pub(crate)` so that the test module and commands.rs can
// reach into them directly when needed (e.g. `db::attempt::save_answer`).
// External crates should only use the re-exported public API below.
pub(crate) mod attempt;
pub(crate) mod helpers;
pub(crate) mod question_bank;
pub(crate) mod schema;
pub(crate) mod search;
pub(crate) mod settings;

#[cfg(test)]
mod tests;

use std::sync::{Arc, Mutex};
use std::{fs, time::Duration};

use rusqlite::Connection;
use tauri::{AppHandle, Manager};

use super::error::ResultExt;

pub use attempt::{
    create_test_attempt, fetch_responses_by_attempt_id, fetch_test_attempt, finalize_submission,
    list_test_attempt_history, pause_test, resume_test, save_answer, toggle_flag,
    update_time_remaining,
};
pub use helpers::now_ms;
pub use question_bank::{
    delete_question_bank, fetch_question_bank, fetch_question_bank_with_questions,
    fetch_question_banks, fetch_questions_by_bank_id, import_question_bank, question_id_conflicts,
};
pub use search::{
    invalidate_search_index, question_main_tags, question_taxonomy_tags, search_questions_cached,
    SearchIndexState,
};
pub use settings::{load_settings, save_settings};

/// Shared result alias used across all DB sub-modules.
pub(crate) type DbResult<T> = Result<T, String>;

/// Shared database handle stored in Tauri state (#13 / #21).
///
/// Wraps a single `rusqlite::Connection` behind a `Mutex` so that all
/// commands share the same connection instead of opening a new one on
/// every invocation.  SQLite writes are inherently serialised, so a
/// mutex is the correct synchronisation primitive here.
#[derive(Clone)]
pub struct DbState(pub Arc<Mutex<Connection>>);

/// Initialise the database and return a `DbState` suitable for
/// `app.manage(…)`.
///
/// Call this once during app startup; the returned value should be
/// stored in Tauri's managed state.
pub fn init_database(app: &AppHandle) -> DbResult<DbState> {
    let conn = open_connection(app)?;
    Ok(DbState(Arc::new(Mutex::new(conn))))
}

/// Open (or create) the SQLite database, enable WAL + FK, and run
/// migrations.
///
/// DESIGN NOTES:
/// - `busy_timeout(5s)`: prevents immediate SQLITE_BUSY errors when
///   the mutex is released between reads but a prior write hasn't
///   committed yet (rare in single-user, but defensive).
/// - `journal_mode = WAL`: enables concurrent readers while a write
///   is in progress — important because timer persistence fires
///   periodically on a background thread.
/// - `foreign_keys = ON`: SQLite disables FKs by default; we need
///   them for cascading deletes (question bank → questions, etc.).
fn open_connection(app: &AppHandle) -> DbResult<Connection> {
    let db_path = database_path(app)?;

    if let Some(parent) = db_path.parent() {
        fs::create_dir_all(parent).stringify_err()?;
    }

    let conn = Connection::open(&db_path).stringify_err()?;
    conn.busy_timeout(Duration::from_secs(5)).stringify_err()?;
    conn.pragma_update(None, "foreign_keys", "ON")
        .stringify_err()?;
    conn.pragma_update(None, "journal_mode", "WAL")
        .stringify_err()?;
    schema::run_migrations(&conn)?;

    Ok(conn)
}

fn database_path(app: &AppHandle) -> DbResult<std::path::PathBuf> {
    let config_dir = app.path().app_config_dir().stringify_err()?;
    Ok(config_dir.join("loop.db"))
}

// ── Row structs shared between sub-modules ──────────────────────────────
//
// These are intermediate representations that map 1:1 to SQLite row
// columns.  They exist because rusqlite's `query_row` closure must
// return a single owned type — we can't construct the domain type
// (e.g. `TestAttempt`) directly inside the closure because `TryFrom`
// conversions (mode, status) are fallible and return `Result<_, String>`,
// which doesn't implement `From<rusqlite::Error>`.

#[derive(Debug)]
pub(crate) struct QuestionRow {
    pub id: String,
    pub question_type: String,
    pub question: String,
    pub options: Option<String>, // JSON-serialised Vec<QuestionOption>
    pub correct_answers: String, // JSON-serialised Vec<String>
    pub explanation: String,
    pub marks: f64,
    pub negative_marks: f64,
    pub negative_marks_unanswered: f64,
    pub time_estimate: Option<i64>, // seconds; NULL = no estimate
    pub difficulty: Option<String>, // "easy" | "medium" | "hard" | NULL
    pub tags: Option<String>,       // JSON-serialised Vec<String>
}

#[derive(Debug)]
pub(crate) struct AttemptRow {
    pub id: String,
    pub bank_id: String,
    pub mode: String,
    pub status: String,
    pub duration: i64,
    pub time_remaining: i64,
    pub started_at: i64,
    pub completed_at: Option<i64>,
    pub score: Option<f64>,
    pub max_score: Option<f64>,
}

#[derive(Debug)]
pub(crate) struct ResponseRow {
    pub question_id: String,
    pub answer: Option<String>,
    pub is_flagged: i64,
}
