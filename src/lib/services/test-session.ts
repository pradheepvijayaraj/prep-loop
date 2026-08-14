/**
 * Test session service \u2014 Tauri IPC wrappers for test attempt operations.
 *
 * These functions are the frontend\u2019s interface to the backend\u2019s
 * attempt/response CRUD (attempt.rs).  The test-session *store*
 * ($lib/stores/test-session.svelte.ts) calls these functions and
 * manages optimistic UI / rollback on top of them.
 */
import type {
  TestAttempt,
  TestAttemptHistoryEntry,
  TestMode,
} from "$lib/types";
import { invokeBackend } from "$lib/services/backend";

/** Answer value: a single string, array of strings, or null (cleared). */
type SavedAnswer = string | string[] | null;

export interface SubmitResult {
  score: number;
  maxScore: number;
}

export async function createTestAttempt(
  bankId: string,
  mode: TestMode,
  durationOverride?: number,
): Promise<string> {
  return invokeBackend<string>("create_test_attempt", {
    bankId,
    mode,
    durationOverride,
  });
}

export async function listTestAttemptHistory(): Promise<
  TestAttemptHistoryEntry[]
> {
  return invokeBackend<TestAttemptHistoryEntry[]>("list_test_attempt_history");
}

export async function saveAnswer(
  attemptId: string,
  questionId: string,
  answer: SavedAnswer,
): Promise<void> {
  await invokeBackend("save_answer", {
    attemptId,
    questionId,
    answer,
  });
}

export async function toggleFlag(
  attemptId: string,
  questionId: string,
): Promise<boolean> {
  return invokeBackend<boolean>("toggle_flag", {
    attemptId,
    questionId,
  });
}

export async function updateTimeRemaining(
  attemptId: string,
  timeRemaining: number,
): Promise<void> {
  await invokeBackend("update_time_remaining", {
    attemptId,
    timeRemaining,
  });
}

export async function pauseTest(
  attemptId: string,
  timeRemaining: number,
): Promise<void> {
  await invokeBackend("pause_test", {
    attemptId,
    timeRemaining,
  });
}

export async function resumeTest(attemptId: string): Promise<void> {
  await invokeBackend("resume_test", {
    attemptId,
  });
}

export async function submitTest(attemptId: string): Promise<SubmitResult> {
  return invokeBackend<SubmitResult>("submit_test", {
    attemptId,
  });
}

export async function getTestAttempt(id: string): Promise<TestAttempt | null> {
  return invokeBackend<TestAttempt | null>("get_test_attempt", {
    attemptId: id,
  });
}
