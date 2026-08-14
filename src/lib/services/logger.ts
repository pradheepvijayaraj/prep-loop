/**
 * Logging utilities.
 *
 * Wraps Tauri's log plugin so the rest of the codebase can call
 * `logError(msg, err)` without worrying about serialisation or
 * whether the plugin is available.
 */
import { error as writeErrorLog } from "@tauri-apps/plugin-log";

/** Safely convert an unknown error value to a loggable string. */
function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

export async function logError(
  message: string,
  error?: unknown,
): Promise<void> {
  const detail =
    error === undefined ? message : `${message}: ${toErrorMessage(error)}`;

  try {
    await writeErrorLog(detail);
  } catch {
    // Keep diagnostics available when the native plugin is unavailable
    // (for example in browser previews and test environments).
    console.error(detail);
  }
}
