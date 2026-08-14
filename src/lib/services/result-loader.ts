import { getQuestionBank } from "$lib/services/question-bank";
import { getTestAttempt } from "$lib/services/test-session";

export async function loadResultContext(attemptId: string) {
  const attempt = await getTestAttempt(attemptId);
  if (!attempt) throw new Error("Test attempt not found");

  const bank = await getQuestionBank(attempt.bankId);
  if (!bank) throw new Error("Set not found");

  return { attempt, bank };
}
