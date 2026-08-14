//! Schema creation and versioned migrations (#17).
//!
//! Each migration is a function that runs inside a transaction.
//! `run_migrations` checks the current schema version and applies any
//! outstanding migrations in order.

use rusqlite::{params, Connection, OptionalExtension};

use super::helpers::table_has_column;
use super::DbResult;
use crate::backend::error::ResultExt;

/// Current schema version.  Bump this whenever a new migration is added.
///
/// HOW TO ADD A MIGRATION:
/// 1. Increment `SCHEMA_VERSION` by 1.
/// 2. Add a `migrate_v<N>` function below the existing ones.
/// 3. Add an `if current < N { migrate_v<N>(conn)?; set_schema_version(conn, N)?; }`
///    block in `run_migrations`.
/// 4. Add a test in `tests.rs` to verify the migration on an in-memory DB.
type Migration = fn(&Connection) -> DbResult<()>;
const MIGRATIONS: &[Migration] = &[
    migrate_v1,
    migrate_v2,
    migrate_v3,
    migrate_v4_repair_foreign_keys,
];
const SCHEMA_VERSION: i64 = MIGRATIONS.len() as i64;

/// Run all outstanding migrations.
pub fn run_migrations(conn: &Connection) -> DbResult<()> {
    // Ensure the version-tracking table exists.
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );",
    )
    .stringify_err()?;

    let current = get_schema_version(conn)?;
    if !(0..=SCHEMA_VERSION).contains(&current) {
        return Err(format!(
            "Unsupported database schema version {current}; latest is {SCHEMA_VERSION}"
        ));
    }
    for (index, migration) in MIGRATIONS.iter().enumerate().skip(current as usize) {
        migration(conn)?;
        set_schema_version(conn, (index + 1) as i64)?;
    }

    // Indices are created outside of versioned migrations because they're
    // idempotent (`IF NOT EXISTS`) and don't need version tracking.
    // Add new indices here freely without bumping SCHEMA_VERSION.
    conn.execute_batch(
        "
        CREATE INDEX IF NOT EXISTS idx_questions_bank_id ON questions(bank_id);
        CREATE INDEX IF NOT EXISTS idx_test_attempts_bank_id ON test_attempts(bank_id);
        ",
    )
    .stringify_err()?;

    Ok(())
}

// ── Migrations ──────────────────────────────────────────────────────────

/// V1: initial schema (all core tables).
///
/// Uses `CREATE TABLE IF NOT EXISTS` so this migration is safe to re-run
/// on databases that were created before the migration system existed.
/// New databases also start here because `schema_version` defaults to 0.
fn migrate_v1(conn: &Connection) -> DbResult<()> {
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS question_banks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            exam TEXT NOT NULL,
            metadata TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            default_duration INTEGER NOT NULL,
            imported_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            color TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answers TEXT NOT NULL,
            explanation TEXT NOT NULL DEFAULT '',
            marks REAL NOT NULL,
            negative_marks REAL NOT NULL DEFAULT 0,
            negative_marks_unanswered REAL NOT NULL DEFAULT 0,
            time_estimate INTEGER,
            difficulty TEXT,
            tags TEXT,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS test_attempts (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            duration INTEGER NOT NULL,
            time_remaining INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            completed_at INTEGER,
            score REAL,
            max_score REAL,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id)
        );

        CREATE TABLE IF NOT EXISTS question_responses (
            id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            answer TEXT,
            is_correct INTEGER,
            is_flagged INTEGER NOT NULL DEFAULT 0,
            time_spent INTEGER,
            FOREIGN KEY (attempt_id) REFERENCES test_attempts(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        ",
    )
    .stringify_err()
}

/// V2: add `category_id` column to `question_banks`.
fn migrate_v2(conn: &Connection) -> DbResult<()> {
    if table_has_column(conn, "question_banks", "category_id")? {
        return Ok(());
    }

    conn.execute("ALTER TABLE question_banks ADD COLUMN category_id TEXT", [])
        .stringify_err()?;

    Ok(())
}

/// V3: remove the abandoned category model and store only non-empty responses.
///
/// Correctness is derived when a submission is scored, so persisting it on
/// every response duplicated source-of-truth data. `time_spent` was never read.
/// The composite primary key also removes the synthetic response UUID and the
/// separate attempt index. Question options, answers and tags remain compact
/// JSON arrays because they are owned by one question and are always read with
/// it; splitting those arrays into child tables would add joins and row/index
/// overhead without reducing duplication.
fn migrate_v3(conn: &Connection) -> DbResult<()> {
    if !table_has_column(conn, "question_banks", "category_id")?
        && !table_has_column(conn, "question_responses", "id")?
    {
        return Ok(());
    }

    conn.execute_batch("PRAGMA foreign_keys = OFF;")
        .stringify_err()?;

    let migration = conn.execute_batch(
        "
        BEGIN IMMEDIATE;

        CREATE TABLE question_banks_v3 (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            exam TEXT NOT NULL,
            metadata TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            default_duration INTEGER NOT NULL,
            imported_at INTEGER NOT NULL
        );

        CREATE TABLE questions_v3 (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answers TEXT NOT NULL,
            explanation TEXT NOT NULL DEFAULT '',
            marks REAL NOT NULL,
            negative_marks REAL NOT NULL DEFAULT 0,
            negative_marks_unanswered REAL NOT NULL DEFAULT 0,
            time_estimate INTEGER,
            difficulty TEXT,
            tags TEXT,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );

        CREATE TABLE test_attempts_v3 (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            duration INTEGER NOT NULL,
            time_remaining INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            completed_at INTEGER,
            score REAL,
            max_score REAL,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );

        CREATE TABLE question_responses_v3 (
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            answer TEXT,
            is_flagged INTEGER NOT NULL DEFAULT 0 CHECK (is_flagged IN (0, 1)),
            PRIMARY KEY (attempt_id, question_id),
            FOREIGN KEY (attempt_id) REFERENCES test_attempts_v3(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions_v3(id) ON DELETE CASCADE
        ) WITHOUT ROWID;

        INSERT INTO question_banks_v3
        SELECT id, name, exam, metadata, total_questions, difficulty,
               default_duration, imported_at
        FROM question_banks;

        INSERT INTO questions_v3
        SELECT id, bank_id, type, question, NULLIF(options, '[]'), correct_answers,
               explanation, marks, negative_marks, negative_marks_unanswered,
               NULLIF(time_estimate, 0), NULLIF(difficulty, ''), NULLIF(tags, '[]')
        FROM questions;

        INSERT INTO test_attempts_v3
        SELECT id, bank_id, mode, status, duration, time_remaining, started_at,
               completed_at, score, max_score
        FROM test_attempts;

        INSERT INTO question_responses_v3 (attempt_id, question_id, answer, is_flagged)
        SELECT attempt_id, question_id, answer, is_flagged
        FROM question_responses
        WHERE answer IS NOT NULL OR is_flagged != 0;

        DROP TABLE question_responses;
        DROP TABLE test_attempts;
        DROP TABLE questions;
        DROP TABLE question_banks;
        DROP TABLE IF EXISTS categories;

        ALTER TABLE question_banks_v3 RENAME TO question_banks;
        ALTER TABLE questions_v3 RENAME TO questions;
        ALTER TABLE test_attempts_v3 RENAME TO test_attempts;
        ALTER TABLE question_responses_v3 RENAME TO question_responses;

        COMMIT;
        ",
    );

    if migration.is_err() {
        let _ = conn.execute_batch("ROLLBACK;");
    }
    conn.execute_batch("PRAGMA foreign_keys = ON;")
        .stringify_err()?;
    migration.stringify_err()?;
    // Dropping tables only creates free pages. VACUUM physically compacts the
    // existing database once after this migration; optimize refreshes planner
    // statistics for the new schema.
    conn.execute_batch("VACUUM; PRAGMA optimize;")
        .stringify_err()?;

    Ok(())
}

/// V4: repair databases created by the original V3 migration.
///
/// SQLite retained references to the temporary `question_banks_v3` table when
/// that migration renamed it to `question_banks`. Rebuild the compact tables
/// with stable references to their final names. The migration is a no-op for
/// databases whose foreign-key metadata is already correct.
fn migrate_v4_repair_foreign_keys(conn: &Connection) -> DbResult<()> {
    let has_legacy_reference = ["questions", "test_attempts", "question_responses"]
        .iter()
        .try_fold(false, |found, table| -> DbResult<bool> {
            if found {
                return Ok(true);
            }

            let mut stmt = conn
                .prepare(&format!("PRAGMA foreign_key_list({table})"))
                .stringify_err()?;
            let mut rows = stmt.query([]).stringify_err()?;
            while let Some(row) = rows.next().stringify_err()? {
                let referenced_table: String = row.get(2).stringify_err()?;
                if referenced_table.ends_with("_v3") {
                    return Ok(true);
                }
            }
            Ok(false)
        })?;

    if !has_legacy_reference {
        return Ok(());
    }

    conn.execute_batch("PRAGMA foreign_keys = OFF;")
        .stringify_err()?;

    let migration = conn.execute_batch(
        "
        BEGIN IMMEDIATE;

        CREATE TABLE question_banks_repaired (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            exam TEXT NOT NULL,
            metadata TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            default_duration INTEGER NOT NULL,
            imported_at INTEGER NOT NULL
        );

        CREATE TABLE questions_repaired (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            type TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answers TEXT NOT NULL,
            explanation TEXT NOT NULL DEFAULT '',
            marks REAL NOT NULL,
            negative_marks REAL NOT NULL DEFAULT 0,
            negative_marks_unanswered REAL NOT NULL DEFAULT 0,
            time_estimate INTEGER,
            difficulty TEXT,
            tags TEXT,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );

        CREATE TABLE test_attempts_repaired (
            id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            duration INTEGER NOT NULL,
            time_remaining INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            completed_at INTEGER,
            score REAL,
            max_score REAL,
            FOREIGN KEY (bank_id) REFERENCES question_banks(id) ON DELETE CASCADE
        );

        CREATE TABLE question_responses_repaired (
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            answer TEXT,
            is_flagged INTEGER NOT NULL DEFAULT 0 CHECK (is_flagged IN (0, 1)),
            PRIMARY KEY (attempt_id, question_id),
            FOREIGN KEY (attempt_id) REFERENCES test_attempts(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        ) WITHOUT ROWID;

        INSERT INTO question_banks_repaired SELECT * FROM question_banks;
        INSERT INTO questions_repaired SELECT * FROM questions;
        INSERT INTO test_attempts_repaired SELECT * FROM test_attempts;
        INSERT INTO question_responses_repaired
            SELECT attempt_id, question_id, answer, is_flagged
            FROM question_responses;

        DROP TABLE question_responses;
        DROP TABLE test_attempts;
        DROP TABLE questions;
        DROP TABLE question_banks;

        ALTER TABLE question_banks_repaired RENAME TO question_banks;
        ALTER TABLE questions_repaired RENAME TO questions;
        ALTER TABLE test_attempts_repaired RENAME TO test_attempts;
        ALTER TABLE question_responses_repaired RENAME TO question_responses;

        COMMIT;
        ",
    );

    if migration.is_err() {
        let _ = conn.execute_batch("ROLLBACK;");
    }
    conn.execute_batch("PRAGMA foreign_keys = ON;")
        .stringify_err()?;
    migration.stringify_err()?;

    Ok(())
}

// ── Version helpers ─────────────────────────────────────────────────────

fn get_schema_version(conn: &Connection) -> DbResult<i64> {
    let version: Option<i64> = conn
        .query_row("SELECT version FROM schema_version LIMIT 1", [], |row| {
            row.get(0)
        })
        .optional()
        .stringify_err()?;

    Ok(version.unwrap_or(0))
}

fn set_schema_version(conn: &Connection, version: i64) -> DbResult<()> {
    // Simple delete+insert instead of upsert because this table only
    // ever holds a single row.  Wrapping in a transaction is unnecessary
    // because this runs inside the outer migration flow which is already
    // serialised by the Mutex<Connection>.
    conn.execute("DELETE FROM schema_version", [])
        .stringify_err()?;
    conn.execute(
        "INSERT INTO schema_version (version) VALUES (?1)",
        params![version],
    )
    .stringify_err()?;

    Ok(())
}
