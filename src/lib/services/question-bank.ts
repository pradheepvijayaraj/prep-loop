/**
 * Question bank service \u2014 CRUD wrappers for question banks.
 *
 * Provides import, fetch, delete, and display helpers for question
 * banks.  Validation is delegated to the backend (validation.rs).
 */
import type {
  ImportResult,
  QuestionBankWithQuestions,
  StoredQuestionBank,
} from "$lib/types";
import { invokeBackend } from "$lib/services/backend";

export async function importQuestionBank(
  jsonContent: string,
): Promise<ImportResult> {
  return invokeBackend<ImportResult>("import_question_bank", {
    jsonContent,
  });
}

export async function getQuestionBanks(): Promise<StoredQuestionBank[]> {
  return invokeBackend<StoredQuestionBank[]>("get_question_banks");
}

export async function getQuestionBank(
  id: string,
): Promise<StoredQuestionBank | null> {
  return invokeBackend<StoredQuestionBank | null>("get_question_bank", {
    bankId: id,
  });
}

export async function getQuestionBankWithQuestions(
  id: string,
): Promise<QuestionBankWithQuestions | null> {
  return invokeBackend<QuestionBankWithQuestions | null>(
    "get_question_bank_with_questions",
    {
      bankId: id,
    },
  );
}

export async function deleteQuestionBank(id: string): Promise<void> {
  await invokeBackend("delete_question_bank", {
    bankId: id,
  });
}
