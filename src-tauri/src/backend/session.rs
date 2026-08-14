//! Session utilities: payload assembly for frontend hydration and
//! keyboard shortcut answer computation.
//!
//! These functions are stateless helpers called from `commands.rs`.
//! They don't touch the database — they transform already-fetched data
//! into the shapes the frontend expects.

use super::types::{AnswerEntry, LoadedSessionPayload, Question, ResponseState, TestAttempt};

/// Assemble the full payload needed to resume a test session.
///
/// The frontend needs the attempt metadata, the ordered question list,
/// the user's saved answers (as `[{ questionId, answer }]`), and the
/// list of flagged question IDs.  This function extracts those from
/// the raw response rows.
pub fn build_loaded_session_payload(
    attempt: TestAttempt,
    questions: Vec<Question>,
    responses: Vec<ResponseState>,
) -> LoadedSessionPayload {
    let answers = responses
        .iter()
        .filter_map(|response| {
            response.answer.clone().map(|answer| AnswerEntry {
                question_id: response.question_id.clone(),
                answer,
            })
        })
        .collect();

    let flags = responses
        .into_iter()
        .filter(|response| response.is_flagged)
        .map(|response| response.question_id)
        .collect();

    LoadedSessionPayload {
        attempt,
        questions,
        answers,
        flags,
    }
}
