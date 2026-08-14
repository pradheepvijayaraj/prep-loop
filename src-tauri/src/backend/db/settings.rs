//! User settings CRUD.
//!
//! Settings are stored as key-value pairs in the `settings` table rather
//! than as columns on a single row.  This makes adding new settings a
//! code-only change (no schema migration needed).  The trade-off is that
//! we must manually map between DB keys (camelCase strings) and the
//! `Settings` struct fields.

use rusqlite::{params, Connection};

use super::helpers::upsert_setting;
use super::DbResult;
use crate::backend::error::ResultExt;
use crate::backend::types::{Settings, SettingsPatch};

/// Load all settings from the database, applying defaults for any
/// missing keys.
pub fn load_settings(conn: &Connection) -> DbResult<Settings> {
    let mut stmt = conn
        .prepare("SELECT key, value FROM settings")
        .stringify_err()?;
    let mut rows = stmt.query([]).stringify_err()?;
    let mut settings = Settings::default();

    while let Some(row) = rows.next().stringify_err()? {
        let key: String = row.get("key").stringify_err()?;
        let value: String = row.get("value").stringify_err()?;

        match key.as_str() {
            "theme" => {
                if matches!(value.as_str(), "system" | "light" | "dark") {
                    settings.theme = value;
                }
            }
            "navigatorExpanded" => settings.navigator_expanded = value == "true",
            "lastLibrarySelectionId" => {
                if !value.is_empty() {
                    settings.last_library_selection_id = Some(value);
                }
            }
            "practiceShowImmediateFeedback" => {
                settings.practice_show_immediate_feedback = value == "true"
            }
            "autoSubmitOnTimerEnd" => settings.auto_submit_on_timer_end = value == "true",
            _ => {}
        }
    }

    Ok(settings)
}

/// Persist a partial settings patch (only provided fields are updated).
///
/// Uses a transaction so that all changed keys are committed atomically.
/// If validation fails mid-patch (e.g. bad theme), the transaction
/// aborts cleanly via early return.
pub fn save_settings(conn: &mut Connection, patch: SettingsPatch) -> DbResult<()> {
    let tx = conn.transaction().stringify_err()?;

    if let Some(theme) = patch.theme {
        if !matches!(theme.as_str(), "system" | "light" | "dark") {
            return Err(format!("Unsupported theme: {theme}"));
        }

        tx.execute(
            "INSERT INTO settings (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            params!["theme", theme],
        )
        .stringify_err()?;
    }

    if let Some(navigator_expanded) = patch.navigator_expanded {
        upsert_setting(&tx, "navigatorExpanded", &navigator_expanded.to_string())?;
    }

    if let Some(last_library_selection_id) = patch.last_library_selection_id {
        upsert_setting(&tx, "lastLibrarySelectionId", &last_library_selection_id)?;
    }

    if let Some(practice_feedback) = patch.practice_show_immediate_feedback {
        upsert_setting(
            &tx,
            "practiceShowImmediateFeedback",
            &practice_feedback.to_string(),
        )?;
    }

    if let Some(auto_submit) = patch.auto_submit_on_timer_end {
        upsert_setting(&tx, "autoSubmitOnTimerEnd", &auto_submit.to_string())?;
    }

    tx.commit().stringify_err()
}
