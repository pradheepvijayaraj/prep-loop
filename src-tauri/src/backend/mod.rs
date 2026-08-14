//! Backend module — all server-side logic for the Tauri app.
//!
//! Architecture overview:
//! - `commands` — Tauri `#[tauri::command]` handlers (thin wrappers).
//! - `db`       — SQLite persistence layer (split into sub-modules).
//! - `scoring`  — Answer evaluation and test result computation.
//! - `session`  — Session payload assembly for frontend hydration.
//! - `validation` — JSON question bank validation before import.
//! - `types`    — Shared data structures (serde-annotated).
//! - `error`    — Error conversion utilities.
//!
//! Visibility rules:
//! - `pub` — accessed from `lib.rs` (e.g. `commands`, `db::DbState`).
//! - `pub(crate)` — internal but used across sibling modules.
//! - private — used only within the declaring module.

pub mod commands;
pub mod db;
mod error; // pub(crate) access via `crate::backend::error::ResultExt`
mod scoring; // pub(crate) access via `crate::backend::scoring::*`
mod session; // only used by commands.rs
pub mod types;
mod validation; // only used by commands.rs
