/**
 * Session page helpers \u2014 data fetching and hydration for test/practice pages.
 *
 * `loadSessionData` fetches the full session payload from the backend and
 * converts raw JSON arrays into the Maps / Sets the store expects.
 */
import { invokeBackend } from "$lib/services/backend";
import type { Question, TestAttempt } from "$lib/types";

export interface LoadedSessionData {
  attempt: TestAttempt;
  questions: Question[];
  answers: Map<string, string | string[]>;
  flags: Set<string>;
}

export interface LoadedSessionResult {
  error?: string;
  redirectTo?: string;
  data?: LoadedSessionData;
}

interface AnswerEntry {
  questionId: string;
  answer: string | string[];
}

interface LoadedSessionPayload {
  attempt: TestAttempt;
  questions: Question[];
  answers: AnswerEntry[];
  flags: string[];
}

function hydrateSessionData(
  payload: LoadedSessionPayload,
): Pick<LoadedSessionData, "attempt" | "questions" | "answers" | "flags"> {
  const answers = new Map<string, string | string[]>();
  for (const entry of payload.answers) {
    answers.set(entry.questionId, entry.answer);
  }

  return {
    attempt: payload.attempt,
    questions: payload.questions,
    answers,
    flags: new Set(payload.flags),
  };
}

export async function loadSessionData(
  attemptId: string,
  missingAttemptMessage: string,
): Promise<LoadedSessionResult> {
  const payload = await invokeBackend<LoadedSessionPayload | null>(
    "get_session_payload",
    {
      attemptId,
    },
  );

  if (!payload) {
    return { error: missingAttemptMessage };
  }

  if (payload.attempt.status === "completed") {
    return { redirectTo: `/results/${attemptId}` };
  }

  return {
    data: hydrateSessionData(payload),
  };
}
