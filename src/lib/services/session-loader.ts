/**
 * Session loader \u2014 orchestrates loading a test/practice session.\n *
 * Fetches the attempt, questions, answers, and flags from the backend,
 * then initialises the test-session store.  Returns a redirect URL if
 * the attempt is already completed, or an error string on failure.
 */
import { loadSessionData } from "$lib/services/session-page";
import type { LoadedSessionData } from "$lib/services/session-page";
import type { TestMode } from "$lib/types";
import { withLoadingTimeout } from "$lib/services/loading-timeout";

export async function loadSession(
  attemptId: string,
  mode: TestMode,
): Promise<{ error?: string; redirectTo?: string; data?: LoadedSessionData }> {
  const modeLabel = mode === "test" ? "Test" : "Practice";
  const result = await loadSessionData(
    attemptId,
    `${modeLabel} session not found`,
  );

  if (result.redirectTo) {
    return { redirectTo: result.redirectTo };
  }

  if (!result.data) {
    return { error: result.error ?? `Failed to load ${mode} session` };
  }

  return { data: result.data };
}

export async function loadSessionWithTimeout(
  attemptId: string,
  mode: TestMode,
): ReturnType<typeof loadSession> {
  return withLoadingTimeout(loadSession(attemptId, mode));
}
