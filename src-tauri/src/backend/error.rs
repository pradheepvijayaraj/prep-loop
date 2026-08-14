//! Error utilities for the backend.
//!
//! Library errors are logged internally and converted to a stable,
//! user-safe message at the command boundary.
//!
//! FUTURE IMPROVEMENT: Replace `String` error returns with a proper
//! domain error enum (e.g. `LoopError::DbError`, `LoopError::NotFound`)
//! and implement `serde::Serialize` so the frontend can pattern-match
//! on error types rather than parsing strings.

/// Extension trait for converting library errors into user-safe strings.
///
/// All errors flowing through `stringify_err` are assumed to originate from
/// external libraries (rusqlite, serde_json, std::io).  The raw message is
/// logged through the configured `log` facade while a generic, user-safe
/// message is returned to the frontend.
///
/// Domain-specific errors (e.g. "Question bank not found") are returned
/// via direct `Err("...".to_string())` and do NOT pass through this trait.
pub trait ResultExt<T> {
    fn stringify_err(self) -> Result<T, String>;
}

impl<T, E: std::fmt::Display> ResultExt<T> for Result<T, E> {
    fn stringify_err(self) -> Result<T, String> {
        self.map_err(|error| {
            let detail = error.to_string();
            // Log the raw error for debugging; it may contain SQL fragments
            // or other internal details that should not reach the UI (#16).
            log::error!("Internal backend error: {detail}");
            "An internal error occurred".to_string()
        })
    }
}
