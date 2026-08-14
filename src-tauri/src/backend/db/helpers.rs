//! Shared helpers: parsing, time and SQL utilities.

use rusqlite::{params, Connection};
use serde::de::DeserializeOwned;

use super::DbResult;
use crate::backend::error::ResultExt;

/// Parse a JSON string into the target type, returning a labelled error.
pub(crate) fn parse_json<T: DeserializeOwned>(value: &str, label: &str) -> DbResult<T> {
    serde_json::from_str(value).map_err(|error| format!("Failed to parse {label}: {error}"))
}

/// Current time in milliseconds since UNIX epoch.
pub fn now_ms() -> i64 {
    let now = std::time::SystemTime::now();
    let duration = now
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    duration.as_millis() as i64
}

/// Convert a domain-error string into a `rusqlite::Error` so it can
/// propagate through `query_row` closures.
pub(crate) fn to_sql_error(error: String) -> rusqlite::Error {
    rusqlite::Error::FromSqlConversionFailure(
        0,
        rusqlite::types::Type::Text,
        Box::new(std::io::Error::new(std::io::ErrorKind::InvalidData, error)),
    )
}

/// Check whether a table has a specific column (#15).
///
/// Uses `PRAGMA table_info` to introspect the schema.  The `table_name`
/// argument is **not** user-supplied (all call sites pass string literals),
/// so the `format!` interpolation is safe from injection.
pub(crate) fn table_has_column(
    conn: &Connection,
    table_name: &str,
    column_name: &str,
) -> DbResult<bool> {
    // Safety note (#15): `table_name` is always a compile-time literal
    // originating from our own code, never from user input.
    let pragma = format!("PRAGMA table_info({table_name})");
    let mut stmt = conn.prepare(&pragma).stringify_err()?;
    let mut rows = stmt.query([]).stringify_err()?;

    while let Some(row) = rows.next().stringify_err()? {
        let existing_name: String = row.get("name").stringify_err()?;
        if existing_name == column_name {
            return Ok(true);
        }
    }

    Ok(false)
}

/// Insert or update a key-value setting.
pub(crate) fn upsert_setting(conn: &Connection, key: &str, value: &str) -> DbResult<()> {
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?1, ?2)
         ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        params![key, value],
    )
    .stringify_err()?;
    Ok(())
}
