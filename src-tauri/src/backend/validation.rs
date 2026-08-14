//! Question bank JSON validation.
//!
//! Validation is split into two phases:
//! 1. **Structural** (`deserialize_question_bank`): JSON parsing via serde.
//!    Reports the first structural error (wrong types, missing fields).
//! 2. **Semantic** (`validate_question_bank`): Business rule checks on the
//!    parsed struct.  Collects all errors so the user sees everything at once.
//!
//! Both phases run before any data touches the database.

use super::types::QuestionBank;

// TODO (#7): Consider replacing `Vec<String>` with a structured
// `ValidationError { path: String, message: String }` so the UI can
// highlight exact fields.  Current string errors already embed paths
// (e.g. "questions[0].marks: Marks must be positive") but parsing them
// client-side is fragile.

/// Parse and validate a question bank JSON string.
///
/// Returns `Ok(QuestionBank)` if valid, or `Err(Vec<String>)` with
/// all validation errors.  Used by `import_question_bank` in commands.rs.
pub fn parse_question_bank_json(json_content: &str) -> Result<QuestionBank, Vec<String>> {
    let bank = deserialize_question_bank(json_content)?;
    let errors = validate_question_bank(&bank);

    if errors.is_empty() {
        Ok(bank)
    } else {
        Err(errors)
    }
}

/// Deserialise the raw JSON into a `QuestionBank`.
///
/// NOTE (#8): `serde_path_to_error` reports only the **first** structural
/// error (e.g. wrong type for a field).  This is a limitation of serde's
/// fail-fast parsing; collecting multiple structural errors would require
/// a custom deserialiser or a crate like `serde_valid`.  Semantic errors
/// (missing IDs, wrong option counts, etc.) are fully aggregated by
/// `validate_question_bank` below.
fn deserialize_question_bank(json_content: &str) -> Result<QuestionBank, Vec<String>> {
    let mut deserializer = serde_json::Deserializer::from_str(json_content);

    serde_path_to_error::deserialize(&mut deserializer).map_err(|error| {
        let path = error.path().to_string();
        let message = error.inner().to_string();

        if path.is_empty() {
            vec![message]
        } else {
            vec![format!("{path}: {message}")]
        }
    })
}

/// Semantic validation of a parsed question bank struct.
///
/// Checks business rules that serde can't enforce:
/// - Required fields non-empty
/// - Positive marks/duration
/// - Unique question IDs
/// - Option consistency for choice-based questions
/// - Correct answer IDs match declared options
fn validate_question_bank(bank: &QuestionBank) -> Vec<String> {
    let mut errors = Vec::new();

    if bank.metadata.name.trim().is_empty() {
        errors.push("metadata.name: Question bank name is required".to_string());
    }
    if bank.metadata.exam.trim().is_empty() {
        errors.push("metadata.exam: Exam type is required".to_string());
    }
    if bank.metadata.total_questions <= 0 {
        errors.push("metadata.totalQuestions: Total questions must be positive".to_string());
    }
    if bank.metadata.default_duration <= 0 {
        errors.push(
            "metadata.defaultDuration: Default duration must be positive (in seconds)".to_string(),
        );
    }
    if bank.questions.is_empty() {
        errors.push("questions: At least one question is required".to_string());
    } else if bank.metadata.total_questions > 0
        && bank.metadata.total_questions as usize != bank.questions.len()
    {
        errors.push(
            "metadata.totalQuestions: Total questions in metadata does not match actual question count"
                .to_string(),
        );
    }

    let mut seen_question_ids = std::collections::HashSet::new();

    for (index, question) in bank.questions.iter().enumerate() {
        let base = format!("questions[{index}]");

        if question.id.trim().is_empty() {
            errors.push(format!("{base}.id: Question ID is required"));
        }
        if !seen_question_ids.insert(question.id.clone()) {
            errors.push(format!(
                "{base}.id: Duplicate question ID '{}'",
                question.id
            ));
        }
        if question.question.trim().is_empty() {
            errors.push(format!("{base}.question: Question text is required"));
        }
        if question.correct_answers.is_empty() {
            errors.push(format!(
                "{base}.correctAnswers: At least one correct answer is required"
            ));
        }
        if question.marks <= 0.0 {
            errors.push(format!("{base}.marks: Marks must be positive"));
        }
        if question.negative_marks < 0.0 {
            errors.push(format!(
                "{base}.negativeMarks: Negative marks cannot be negative"
            ));
        }
        if question.negative_marks_unanswered < 0.0 {
            errors.push(format!(
                "{base}.negativeMarksUnanswered: Negative marks for unanswered cannot be negative"
            ));
        }
        if let Some(time_estimate) = question.time_estimate {
            if time_estimate <= 0 {
                errors.push(format!(
                    "{base}.timeEstimate: Time estimate must be positive"
                ));
            }
        }

        let is_choice_question = matches!(
            question.question_type,
            super::types::QuestionType::SingleChoice
                | super::types::QuestionType::MultipleChoice
                | super::types::QuestionType::TrueFalse
        );

        if is_choice_question {
            let Some(options) = question.options.as_ref() else {
                errors.push(format!(
                    "{base}.options: Choice-based questions must have at least 2 options"
                ));
                continue;
            };

            if options.len() < 2 {
                errors.push(format!(
                    "{base}.options: Choice-based questions must have at least 2 options"
                ));
            }

            for (option_index, option) in options.iter().enumerate() {
                if option.id.trim().is_empty() {
                    errors.push(format!(
                        "{base}.options[{option_index}].id: Option ID is required"
                    ));
                }
                if option.text.trim().is_empty() {
                    errors.push(format!(
                        "{base}.options[{option_index}].text: Option text is required"
                    ));
                }
            }

            let option_ids: std::collections::HashSet<&str> =
                options.iter().map(|option| option.id.as_str()).collect();
            if !question
                .correct_answers
                .iter()
                .all(|answer| option_ids.contains(answer.as_str()))
            {
                errors.push(format!(
                    "{base}.correctAnswers: Correct answers must match option IDs"
                ));
            }
        }

        if matches!(
            question.question_type,
            super::types::QuestionType::SingleChoice
        ) && question.correct_answers.len() != 1
        {
            errors.push(format!(
                "{base}.correctAnswers: Single-choice questions must have exactly one correct answer"
            ));
        }

        if matches!(
            question.question_type,
            super::types::QuestionType::TrueFalse
        ) && question
            .options
            .as_ref()
            .map(|options| options.len())
            .unwrap_or_default()
            != 2
        {
            errors.push(format!(
                "{base}.options: True/False questions must have exactly 2 options"
            ));
        }
    }

    errors
}
