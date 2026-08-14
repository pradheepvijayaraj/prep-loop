//! Question bank and question CRUD.
//!
//! A **question bank** is an imported JSON file containing exam metadata
//! and a list of questions.  Banks are immutable after import (questions
//! are not editable). Deleting a bank cascades to its questions and attempts.

use rusqlite::{params, Connection, OptionalExtension};

use super::helpers::{now_ms, parse_json, to_sql_error};
use super::{DbResult, QuestionRow};
use crate::backend::error::ResultExt;
use crate::backend::types::{
    Difficulty, Question, QuestionBank, QuestionBankWithQuestions, QuestionOption, QuestionType,
    StoredQuestionBank,
};

/// Fetch all stored question banks, newest first.
pub fn fetch_question_banks(conn: &Connection) -> DbResult<Vec<StoredQuestionBank>> {
    let mut stmt = conn
        .prepare(
            "SELECT id, name, exam, metadata, total_questions, difficulty, default_duration, imported_at
             FROM question_banks
             ORDER BY imported_at DESC",
        )
        .stringify_err()?;
    let mut rows = stmt.query([]).stringify_err()?;
    let mut banks = Vec::new();

    while let Some(row) = rows.next().stringify_err()? {
        let difficulty: String = row.get("difficulty").stringify_err()?;

        banks.push(StoredQuestionBank {
            id: row.get("id").stringify_err()?,
            name: row.get("name").stringify_err()?,
            exam: row.get("exam").stringify_err()?,
            metadata: row.get("metadata").stringify_err()?,
            total_questions: row.get("total_questions").stringify_err()?,
            difficulty: Difficulty::try_from(difficulty.as_str())?,
            default_duration: row.get("default_duration").stringify_err()?,
            imported_at: row.get("imported_at").stringify_err()?,
        });
    }

    Ok(banks)
}

/// Fetch a single question bank by ID.
pub fn fetch_question_bank(
    conn: &Connection,
    bank_id: &str,
) -> DbResult<Option<StoredQuestionBank>> {
    let mut stmt = conn
        .prepare(
            "SELECT id, name, exam, metadata, total_questions, difficulty, default_duration, imported_at
             FROM question_banks
             WHERE id = ?1",
        )
        .stringify_err()?;

    let bank = stmt
        .query_row(params![bank_id], |row| {
            let difficulty: String = row.get("difficulty")?;

            Ok(StoredQuestionBank {
                id: row.get("id")?,
                name: row.get("name")?,
                exam: row.get("exam")?,
                metadata: row.get("metadata")?,
                total_questions: row.get("total_questions")?,
                difficulty: Difficulty::try_from(difficulty.as_str()).map_err(to_sql_error)?,
                default_duration: row.get("default_duration")?,
                imported_at: row.get("imported_at")?,
            })
        })
        .optional()
        .stringify_err()?;

    Ok(bank)
}

/// Fetch all questions belonging to a question bank, in insertion order.
pub fn fetch_questions_by_bank_id(conn: &Connection, bank_id: &str) -> DbResult<Vec<Question>> {
    let mut stmt = conn
        .prepare(
            "SELECT id, type, question, options, correct_answers, explanation, marks, negative_marks,
                    negative_marks_unanswered, time_estimate, difficulty, tags
             FROM questions
             WHERE bank_id = ?1
             ORDER BY rowid",
        )
        .stringify_err()?;
    let mut rows = stmt.query(params![bank_id]).stringify_err()?;
    let mut questions = Vec::new();

    while let Some(row) = rows.next().stringify_err()? {
        questions.push(question_from_row(QuestionRow {
            id: row.get("id").stringify_err()?,
            question_type: row.get("type").stringify_err()?,
            question: row.get("question").stringify_err()?,
            options: row.get("options").stringify_err()?,
            correct_answers: row.get("correct_answers").stringify_err()?,
            explanation: row.get("explanation").stringify_err()?,
            marks: row.get("marks").stringify_err()?,
            negative_marks: row.get("negative_marks").stringify_err()?,
            negative_marks_unanswered: row.get("negative_marks_unanswered").stringify_err()?,
            time_estimate: row.get("time_estimate").stringify_err()?,
            difficulty: row.get("difficulty").stringify_err()?,
            tags: row.get("tags").stringify_err()?,
        })?);
    }

    Ok(questions)
}

/// Fetch a question bank together with its questions.
pub fn fetch_question_bank_with_questions(
    conn: &Connection,
    bank_id: &str,
) -> DbResult<Option<QuestionBankWithQuestions>> {
    let Some(bank) = fetch_question_bank(conn, bank_id)? else {
        return Ok(None);
    };

    Ok(Some(QuestionBankWithQuestions {
        id: bank.id,
        name: bank.name,
        exam: bank.exam,
        metadata: bank.metadata,
        total_questions: bank.total_questions,
        difficulty: bank.difficulty,
        default_duration: bank.default_duration,
        imported_at: bank.imported_at,
        questions: fetch_questions_by_bank_id(conn, bank_id)?,
    }))
}

/// Import a validated question bank into the database (transactional).
pub fn import_question_bank(conn: &mut Connection, bank: &QuestionBank) -> DbResult<String> {
    let bank_id = uuid::Uuid::new_v4().to_string();
    let imported_at = now_ms();
    // Serialize the full metadata struct to JSON for storage.  The raw
    // JSON is kept so we can round-trip unknown fields added later via
    // the `#[serde(flatten)]` `extra` map on QuestionBankMetadata.
    let metadata = serde_json::to_string(&bank.metadata).stringify_err()?;

    let tx = conn.transaction().stringify_err()?;

    tx.execute(
        "INSERT INTO question_banks (
            id, name, exam, metadata, total_questions, difficulty, default_duration, imported_at
         ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            bank_id,
            bank.metadata.name,
            bank.metadata.exam,
            metadata,
            bank.metadata.total_questions,
            bank.metadata.difficulty.as_str(),
            bank.metadata.default_duration,
            imported_at,
        ],
    )
    .stringify_err()?;

    {
        let mut insert_question = tx
            .prepare(
                "INSERT INTO questions (
                    id, bank_id, type, question, options, correct_answers, explanation, marks,
                    negative_marks, negative_marks_unanswered, time_estimate, difficulty, tags
                 ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
            )
            .stringify_err()?;

        for question in &bank.questions {
            let options = question
                .options
                .as_ref()
                .filter(|options| !options.is_empty())
                .map(serde_json::to_string)
                .transpose()
                .stringify_err()?;
            let correct_answers =
                serde_json::to_string(&question.correct_answers).stringify_err()?;
            let tags = (!question.tags.is_empty())
                .then(|| serde_json::to_string(&question.tags))
                .transpose()
                .stringify_err()?;

            insert_question
                .execute(params![
                    question.id,
                    bank_id,
                    question.question_type.as_str(),
                    question.question,
                    options,
                    correct_answers,
                    question.explanation,
                    question.marks,
                    question.negative_marks,
                    question.negative_marks_unanswered,
                    question.time_estimate,
                    question.difficulty.map(|difficulty| difficulty.as_str()),
                    tags,
                ])
                .stringify_err()?;
        }
    }

    tx.commit().stringify_err()?;
    Ok(bank_id)
}

/// Return user-facing validation errors for IDs already owned by another bank.
pub fn question_id_conflicts(conn: &Connection, bank: &QuestionBank) -> DbResult<Vec<String>> {
    let mut statement = conn
        .prepare("SELECT bank_id FROM questions WHERE id = ?1")
        .stringify_err()?;
    let mut conflicts = Vec::new();
    for (index, question) in bank.questions.iter().enumerate() {
        let owner: Option<String> = statement
            .query_row(params![question.id], |row| row.get(0))
            .optional()
            .stringify_err()?;
        if owner.is_some() {
            conflicts.push(format!(
                "questions[{index}].id: Question ID '{}' is already used by another bank",
                question.id
            ));
        }
    }
    Ok(conflicts)
}

/// Delete a question bank and all associated data (cascading).
pub fn delete_question_bank(conn: &mut Connection, bank_id: &str) -> DbResult<()> {
    if fetch_question_bank(conn, bank_id)?.is_none() {
        return Err("Question bank not found".to_string());
    }

    let tx = conn.transaction().stringify_err()?;
    tx.execute("DELETE FROM question_banks WHERE id = ?1", params![bank_id])
        .stringify_err()?;

    tx.commit().stringify_err()
}

// ── Internal helpers ────────────────────────────────────────────────────

/// Question_from_row: maps raw SQLite columns → the domain `Question` type.
///
/// JSON columns (`options`, `correct_answers`, `tags`) are deserialized
/// here.  An empty options array is normalised to `None` to match the
/// type from the original import JSON (options are only meaningful for
/// choice-based question types).
pub(crate) fn question_from_row(row: QuestionRow) -> DbResult<Question> {
    let options: Vec<QuestionOption> =
        parse_json(row.options.as_deref().unwrap_or("[]"), "question options")?;
    let difficulty = match row.difficulty.as_deref().map(str::trim) {
        Some("") | None => None,
        Some(value) => Some(Difficulty::try_from(value)?),
    };

    Ok(Question {
        id: row.id,
        question_type: QuestionType::try_from(row.question_type.as_str())?,
        question: row.question,
        options: if options.is_empty() {
            None
        } else {
            Some(options)
        },
        correct_answers: parse_json(&row.correct_answers, "correct answers")?,
        explanation: row.explanation,
        marks: row.marks,
        negative_marks: row.negative_marks,
        negative_marks_unanswered: row.negative_marks_unanswered,
        time_estimate: row.time_estimate.filter(|value| *value > 0),
        difficulty,
        tags: parse_json(row.tags.as_deref().unwrap_or("[]"), "question tags")?,
    })
}
