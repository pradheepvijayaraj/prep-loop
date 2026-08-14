import { invokeBackend } from "$lib/services/backend";
import type { QuestionSearchResponse } from "$lib/types";

export async function searchQuestions(
  query: string,
  sections?: string[],
): Promise<QuestionSearchResponse> {
  return invokeBackend<QuestionSearchResponse>("search_questions", {
    query,
    sections,
  });
}

/** Build the reusable SQLite-backed search index before the first keystroke. */
export async function warmQuestionSearch(): Promise<void> {
  await searchQuestions("");
}
