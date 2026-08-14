mod backend;
pub mod semantic;
pub mod taxonomy;

use tauri::Manager;

/// Tauri application entry point.
///
/// STARTUP FLOW:
/// 1. Register application logging.
/// 2. In the `.setup()` hook, open the SQLite database, run migrations,
///    and store the shared connection as managed state (`DbState`).
/// 3. Register all `#[tauri::command]` handlers.
/// 4. Start the event loop.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .setup(|app| {
            // Initialise the shared database connection (#13 / #21).
            // This runs once at startup; the resulting `DbState` is
            // injected into every `#[tauri::command]` via `State<DbState>`.
            let db_state =
                backend::db::init_database(&app.handle()).expect("Failed to initialise database");
            app.manage(db_state);
            app.manage(backend::db::SearchIndexState::default());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend::commands::load_settings,
            backend::commands::save_settings,
            backend::commands::import_question_bank,
            backend::commands::get_question_banks,
            backend::commands::get_question_bank,
            backend::commands::get_question_bank_with_questions,
            backend::commands::search_questions,
            backend::commands::delete_question_bank,
            backend::commands::create_test_attempt,
            backend::commands::list_test_attempt_history,
            backend::commands::save_answer,
            backend::commands::toggle_flag,
            backend::commands::update_time_remaining,
            backend::commands::pause_test,
            backend::commands::resume_test,
            backend::commands::submit_test,
            backend::commands::get_test_attempt,
            backend::commands::calculate_test_result,
            backend::commands::get_question_review,
            backend::commands::get_session_payload,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
