/**
 * Thin wrapper around Tauri's `invoke` API.
 *
 * All backend calls go through this single function so we can
 * centralise future concerns (e.g. error mapping, retry logic,
 * request logging) in one place.
 */
import { invoke } from "@tauri-apps/api/core";

export const BACKEND_COMMANDS = {
  calculate_test_result: "calculate_test_result",
  create_test_attempt: "create_test_attempt",
  delete_question_bank: "delete_question_bank",
  get_question_bank: "get_question_bank",
  get_question_bank_with_questions: "get_question_bank_with_questions",
  get_question_banks: "get_question_banks",
  get_question_review: "get_question_review",
  get_session_payload: "get_session_payload",
  get_test_attempt: "get_test_attempt",
  import_question_bank: "import_question_bank",
  list_test_attempt_history: "list_test_attempt_history",
  load_settings: "load_settings",
  pause_test: "pause_test",
  resume_test: "resume_test",
  save_answer: "save_answer",
  save_settings: "save_settings",
  search_questions: "search_questions",
  submit_test: "submit_test",
  toggle_flag: "toggle_flag",
  update_time_remaining: "update_time_remaining",
} as const;

export type BackendCommand =
  (typeof BACKEND_COMMANDS)[keyof typeof BACKEND_COMMANDS];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireRecord(
  command: BackendCommand,
  value: unknown,
  keys: string[],
): void {
  if (!isRecord(value) || keys.some((key) => !(key in value))) {
    throw new Error(`Invalid response from backend command: ${command}`);
  }
}

function validateBackendResult(command: BackendCommand, value: unknown): void {
  if (
    [
      "save_answer",
      "save_settings",
      "delete_question_bank",
      "pause_test",
      "resume_test",
      "update_time_remaining",
    ].includes(command)
  )
    return;
  if (command === "create_test_attempt" && typeof value === "string") return;
  if (command === "toggle_flag" && typeof value === "boolean") return;
  if (
    ["get_question_bank", "get_test_attempt"].includes(command) &&
    value === null
  )
    return;
  if (command === "get_session_payload" && value === null) return;
  if (
    [
      "get_question_banks",
      "get_question_review",
      "list_test_attempt_history",
    ].includes(command)
  ) {
    if (!Array.isArray(value) || value.some((item) => !isRecord(item))) {
      throw new Error(`Invalid response from backend command: ${command}`);
    }
    return;
  }
  const keysByCommand: Partial<Record<BackendCommand, string[]>> = {
    calculate_test_result: ["attemptId", "score", "maxScore", "totalQuestions"],
    get_question_bank: ["id", "name", "metadata"],
    get_question_bank_with_questions: ["id", "name", "questions"],
    get_session_payload: ["attempt", "questions", "answers", "flags"],
    get_test_attempt: ["id", "bankId", "status"],
    import_question_bank: ["success"],
    load_settings: ["theme"],
    search_questions: ["query", "results", "totalMatches"],
    submit_test: ["score", "maxScore"],
  };
  const required = keysByCommand[command];
  if (required) requireRecord(command, value, required);
}

/**
 * Invoke a Tauri backend command.
 *
 * @typeParam T Return type expected from the backend.
 * @param command Rust command name (must match `#[tauri::command]`).
 * @param args    Optional key-value arguments passed as the `args` object.
 */
export async function invokeBackend<T>(
  command: BackendCommand,
  args?: Record<string, unknown>,
): Promise<T> {
  // Tauri commands in this app expose one `args` parameter. Centralizing that
  // transport envelope prevents individual services from omitting or nesting
  // it incorrectly.
  const result: unknown = await invoke(command, args ? { args } : undefined);
  validateBackendResult(command, result);
  return result as T;
}
