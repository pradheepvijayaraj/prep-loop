//! Integration tests for the database layer.
//!
//! All tests use an in-memory SQLite database so they are fast and
//! isolated.  Each test creates a fresh connection with FK enforcement
//! and runs all migrations from scratch.
//!
//! TEST STRATEGY:
//! - `schema_migration_is_idempotent`: Ensures re-running migrations is safe.
//! - `save_answer_rejects_completed_attempt`: Validates the TOCTOU fix (#14)
//!   by confirming that answers can't be saved after submission.

#[cfg(test)]
mod tests {
    use std::fs;

    use rusqlite::Connection;

    use crate::backend::db::question_bank::import_question_bank;
    use crate::backend::db::schema::run_migrations;
    use crate::backend::db::search::{
        invalidate_search_index, search_questions, search_questions_cached,
        search_questions_scoped, semantic_index_freshness, semantic_tag_coverage, SearchIndexState,
    };
    use crate::backend::types::{
        Difficulty, Question, QuestionBank, QuestionBankMetadata, QuestionType,
    };

    fn setup_conn() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.pragma_update(None, "foreign_keys", "ON").unwrap();
        run_migrations(&conn).unwrap();
        conn
    }

    fn sample_bank() -> QuestionBank {
        QuestionBank {
            metadata: QuestionBankMetadata {
                name: "Sample Bank".to_string(),
                exam: "Mock Exam".to_string(),
                total_questions: 1,
                difficulty: Difficulty::Medium,
                default_duration: 600,
                extra: Default::default(),
            },
            questions: vec![Question {
                id: "q-1".to_string(),
                question_type: QuestionType::SingleChoice,
                question: "Sample question?".to_string(),
                options: Some(vec![
                    crate::backend::types::QuestionOption {
                        id: "a".to_string(),
                        text: "A".to_string(),
                    },
                    crate::backend::types::QuestionOption {
                        id: "b".to_string(),
                        text: "B".to_string(),
                    },
                ]),
                correct_answers: vec!["a".to_string()],
                explanation: "Because".to_string(),
                marks: 2.0,
                negative_marks: 0.5,
                negative_marks_unanswered: 0.0,
                time_estimate: Some(30),
                difficulty: Some(Difficulty::Medium),
                tags: vec!["logic".to_string()],
            }],
        }
    }

    #[test]
    fn schema_migration_is_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        run_migrations(&conn).unwrap();
        // Running migrations a second time should be a no-op (not error)
        // because every CREATE TABLE uses IF NOT EXISTS and the schema_version
        // check skips already-applied migrations.
        run_migrations(&conn).unwrap();
    }

    #[test]
    fn question_search_covers_the_corpus_and_ranks_related_concepts() {
        let mut conn = setup_conn();
        let mut bank = sample_bank();
        bank.metadata.name = "UPSC CSE Mains GS 2 2024".to_string();
        bank.metadata.exam = "UPSC CSE".to_string();
        bank.metadata.total_questions = 2;
        bank.metadata
            .extra
            .insert("year".to_string(), serde_json::json!(2024));
        bank.metadata
            .extra
            .insert("stage".to_string(), serde_json::json!("mains"));
        bank.metadata
            .extra
            .insert("paper".to_string(), serde_json::json!("GS2"));
        bank.metadata
            .extra
            .insert("section".to_string(), serde_json::json!("mains-gs2"));
        bank.questions[0].question =
            "Explain how Parliament ensures constitutional accountability.".to_string();
        bank.questions[0].tags = vec!["constitution".to_string()];

        let mut climate_question = bank.questions[0].clone();
        climate_question.id = "q-2".to_string();
        climate_question.question =
            "Assess the effects of climate change on Himalayan ecology.".to_string();
        climate_question.tags = vec!["environment".to_string()];
        bank.questions.push(climate_question);

        import_question_bank(&mut conn, &bank).unwrap();

        let constitution = search_questions(&conn, "constitutional").unwrap();
        assert_eq!(constitution.searched_questions, 2);
        assert_eq!(constitution.results[0].question_id, "q-1");

        let typo = search_questions(&conn, "parliment").unwrap();
        assert_eq!(typo.results[0].question_id, "q-1");

        let ecology = search_questions(&conn, "ecology").unwrap();
        assert_eq!(ecology.results[0].question_id, "q-2");
    }

    #[test]
    fn question_search_respects_section_scope_and_cache_invalidation() {
        let mut conn = setup_conn();
        let mut prelims_bank = sample_bank();
        prelims_bank.metadata.name = "UPSC CSE Prelims GS 1 2024".to_string();
        prelims_bank.metadata.exam = "UPSC CSE".to_string();
        prelims_bank
            .metadata
            .extra
            .insert("year".to_string(), serde_json::json!(2024));
        prelims_bank
            .metadata
            .extra
            .insert("section".to_string(), serde_json::json!("prelims-gs1"));
        prelims_bank.questions[0].id = "prelims-q-1".to_string();
        prelims_bank.questions[0].question =
            "Which constitutional body audits public expenditure?".to_string();
        import_question_bank(&mut conn, &prelims_bank).unwrap();

        let mut mains_bank = prelims_bank.clone();
        mains_bank.metadata.name = "UPSC CSE Mains GS 2 2024".to_string();
        mains_bank
            .metadata
            .extra
            .insert("section".to_string(), serde_json::json!("mains-gs2"));
        mains_bank.questions[0].id = "mains-q-1".to_string();
        mains_bank.questions[0].question =
            "Discuss constitutional accountability in public expenditure.".to_string();
        import_question_bank(&mut conn, &mains_bank).unwrap();

        let prelims_sections = vec!["prelims-gs1".to_string()];
        let scoped =
            search_questions_scoped(&conn, "constitutional expenditure", Some(&prelims_sections))
                .unwrap();
        assert_eq!(scoped.searched_questions, 1);
        assert_eq!(scoped.results.len(), 1);
        assert_eq!(scoped.results[0].section, "prelims-gs1");

        let cache = SearchIndexState::default();
        let cached =
            search_questions_cached(&conn, &cache, "constitutional", Some(&prelims_sections))
                .unwrap();
        assert_eq!(cached.searched_questions, 1);

        let mut second_prelims = prelims_bank.clone();
        second_prelims.metadata.name = "UPSC CSE Prelims GS 1 2025".to_string();
        second_prelims
            .metadata
            .extra
            .insert("year".to_string(), serde_json::json!(2025));
        second_prelims.questions[0].id = "prelims-q-2".to_string();
        import_question_bank(&mut conn, &second_prelims).unwrap();

        invalidate_search_index(&cache).unwrap();
        let refreshed =
            search_questions_cached(&conn, &cache, "constitutional", Some(&prelims_sections))
                .unwrap();
        assert_eq!(refreshed.searched_questions, 2);
    }

    #[test]
    fn bundled_upsc_corpus_is_fully_searchable_and_similarity_sorted() {
        let mut conn = setup_conn();
        let corpus_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../static/upsc");
        let catalog: serde_json::Value =
            serde_json::from_str(&fs::read_to_string(corpus_root.join("catalog.json")).unwrap())
                .unwrap();
        let papers = catalog["papers"].as_array().unwrap();
        let mut expected_questions = 0usize;
        let mut expected_math_questions = 0usize;

        for paper in papers {
            let relative_path = paper["path"].as_str().unwrap();
            let bank: QuestionBank =
                serde_json::from_str(&fs::read_to_string(corpus_root.join(relative_path)).unwrap())
                    .unwrap();
            expected_questions += bank.questions.len();
            if paper["section"]
                .as_str()
                .is_some_and(|section| section.starts_with("mains-maths"))
            {
                expected_math_questions += bank.questions.len();
            }
            import_question_bank(&mut conn, &bank).unwrap();
        }

        assert!(expected_questions > 4_000);
        let (fresh_semantic_records, indexed_documents) = semantic_index_freshness(&conn).unwrap();
        assert_eq!(indexed_documents, expected_questions);
        assert_eq!(
            fresh_semantic_records, expected_questions,
            "the bundled semantic index is stale; run `bun run semantic:index`"
        );
        let (tagged_documents, indexed_documents) = semantic_tag_coverage(&conn).unwrap();
        assert_eq!(tagged_documents, indexed_documents);
        let search_index = SearchIndexState::default();

        let semantic_metadata: serde_json::Value = serde_json::from_str(
            &fs::read_to_string(
                std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("models/semantic/index.json"),
            )
            .unwrap(),
        )
        .unwrap();

        // Exact taxonomy labels are exhaustive filters. Their result counts
        // come from generated metadata, so every main tag and subtag is
        // checked without maintaining a second hand-written taxonomy list.
        for (main_tag, count) in semantic_metadata["mainTagCounts"].as_object().unwrap() {
            let expected = count.as_u64().unwrap() as usize;
            let response = search_questions_cached(&conn, &search_index, main_tag, None).unwrap();
            assert_eq!(
                response.results.len(),
                expected,
                "incomplete {main_tag} result set"
            );
            assert_eq!(response.total_matches, expected);
            assert!(response
                .results
                .iter()
                .all(|result| result.main_tag == *main_tag));
        }

        for (qualified_subtag, count) in semantic_metadata["subtagCounts"].as_object().unwrap() {
            let (_, subtag) = qualified_subtag
                .split_once(" / ")
                .expect("subtag metadata key must include its main tag");
            let expected = count.as_u64().unwrap() as usize;
            let response = search_questions_cached(&conn, &search_index, subtag, None).unwrap();
            assert_eq!(
                response.results.len(),
                expected,
                "incomplete {subtag} result set"
            );
            assert_eq!(response.total_matches, expected);
            assert!(response.results.iter().all(|result| {
                result
                    .subtags
                    .iter()
                    .any(|result_subtag| result_subtag == subtag)
            }));
        }

        for (section, tag_counts) in semantic_metadata["sectionMainTagCounts"]
            .as_object()
            .unwrap()
        {
            let sections = vec![section.clone()];
            for (main_tag, count) in tag_counts.as_object().unwrap() {
                let expected = count.as_u64().unwrap() as usize;
                let response =
                    search_questions_cached(&conn, &search_index, main_tag, Some(&sections))
                        .unwrap();
                assert_eq!(response.results.len(), expected);
                assert_eq!(response.total_matches, expected);
                assert!(response
                    .results
                    .iter()
                    .all(|result| { result.section == *section && result.main_tag == *main_tag }));
            }
        }

        let normalized_taxonomy_query =
            search_questions_cached(&conn, &search_index, "polity and constitution", None).unwrap();
        let expected_polity = semantic_metadata["mainTagCounts"]["Polity & Constitution"]
            .as_u64()
            .unwrap() as usize;
        assert_eq!(normalized_taxonomy_query.results.len(), expected_polity);

        let response =
            search_questions_cached(&conn, &search_index, "climate change", None).unwrap();
        assert_eq!(response.searched_questions, expected_questions);
        assert!(!response.results.is_empty());
        assert!(response.results.iter().all(|result| {
            !result.main_tag.trim().is_empty()
                && !result.subtags.is_empty()
                && result.subtags.len() <= 3
        }));
        assert!(response
            .results
            .windows(2)
            .all(|pair| pair[0].similarity >= pair[1].similarity));

        let reused_index =
            search_questions_cached(&conn, &search_index, "parliament", None).unwrap();
        assert_eq!(reused_index.searched_questions, expected_questions);
        assert!(!reused_index.results.is_empty());

        let water = search_questions_cached(&conn, &search_index, "water", None).unwrap();
        assert!(water
            .results
            .windows(2)
            .all(|pair| { pair[0].similarity >= pair[1].similarity }));
        assert!(water.results.iter().any(|result| {
            let visible_text = format!(
                "{} {}",
                result.question,
                result
                    .options
                    .iter()
                    .map(|option| option.text.as_str())
                    .collect::<Vec<_>>()
                    .join(" ")
            )
            .to_lowercase();
            !visible_text.contains("water")
                && ["river", "ocean", "sea", "lake", "wetland", "marine"]
                    .iter()
                    .any(|concept| visible_text.contains(concept))
        }));

        let river = search_questions_cached(&conn, &search_index, "river", None).unwrap();
        for (query, expected_question) in [
            ("river", "upsc_2016_gs1_q23"),
            ("ocean", "upsc_2021_gs1_q58"),
            ("groundwater depletion", "upsc_2025_mains_gs3_q12"),
            ("forest conservation", "upsc_2016_gs1_q69"),
            ("inflation", "upsc_2015_gs1_q87"),
            ("parliamentary accountability", "upsc_2018_mains_gs2_q4"),
            ("cross-border cyber attacks", "upsc_2021_mains_gs3_q10"),
            ("maternal health", "upsc_2020_mains_gs2_q6"),
            ("unemployment", "upsc_2023_mains_gs3_q11"),
            ("food security", "upsc_2021_mains_gs3_q13"),
        ] {
            let response = search_questions_cached(&conn, &search_index, query, None).unwrap();
            assert!(
                response
                    .results
                    .iter()
                    .any(|result| result.question_id == expected_question),
                "expected {expected_question} in results for {query}"
            );
        }

        for query in [
            "zxqvplmnr",
            "sourdough pizza recipe",
            "crochet pattern for a stuffed dinosaur",
            "video game speedrunning tutorial",
            "guitar chord fingering exercise",
        ] {
            let response = search_questions_cached(&conn, &search_index, query, None).unwrap();
            assert!(
                response.results.is_empty(),
                "out-of-domain query {query:?} returned {} arbitrary neighbours",
                response.results.len(),
            );
        }

        let former_river_false_positives = [
            "upsc_2024_gs1_q70",
            "upsc_2026_gs1_q100",
            "upsc_2025_gs1_q66",
            "upsc_2013_csat_q35",
        ];
        assert!(river.results.iter().take(40).all(|result| {
            !former_river_false_positives.contains(&result.question_id.as_str())
        }));
        assert!(river
            .results
            .windows(2)
            .all(|pair| { pair[0].similarity >= pair[1].similarity }));
        assert!(river.results.iter().any(|result| {
            let visible_text = format!(
                "{} {}",
                result.question,
                result
                    .options
                    .iter()
                    .map(|option| option.text.as_str())
                    .collect::<Vec<_>>()
                    .join(" ")
            )
            .to_lowercase();
            !visible_text.contains("river")
                && [
                    "water",
                    "ocean",
                    "sea",
                    "lake",
                    "wetland",
                    "marine",
                    "groundwater",
                    "aquifer",
                ]
                .iter()
                .any(|concept| visible_text.contains(concept))
        }));
        assert!(river.results.iter().any(|result| {
            result.main_tag == "Geography"
                && result
                    .subtags
                    .iter()
                    .any(|subtag| subtag.contains("Water") || subtag.contains("Ocean"))
        }));

        let non_math_sections = vec![
            "prelims-gs1".to_string(),
            "prelims-csat".to_string(),
            "mains-essay".to_string(),
            "mains-gs1".to_string(),
            "mains-gs2".to_string(),
            "mains-gs3".to_string(),
            "mains-gs4".to_string(),
        ];
        let non_math_river =
            search_questions_cached(&conn, &search_index, "river", Some(&non_math_sections))
                .unwrap();
        assert_eq!(
            non_math_river.searched_questions,
            expected_questions - expected_math_questions
        );
        assert!(non_math_river
            .results
            .iter()
            .all(|result| result.main_tag != "Mathematics"));

        let math_sections = vec!["mains-maths1".to_string(), "mains-maths2".to_string()];
        let math_search = search_questions_cached(
            &conn,
            &search_index,
            "differential equation",
            Some(&math_sections),
        )
        .unwrap();
        assert_eq!(math_search.searched_questions, expected_math_questions);
        assert!(!math_search.results.is_empty());
        assert!(math_search
            .results
            .iter()
            .all(|result| result.main_tag == "Mathematics"));

        let gs2_sections = vec!["mains-gs2".to_string()];
        let foreign_policy = search_questions_cached(
            &conn,
            &search_index,
            "energy security foreign policy Middle Eastern countries",
            Some(&gs2_sections),
        )
        .unwrap();
        let foreign_policy_question = foreign_policy
            .results
            .iter()
            .find(|result| result.question_id == "upsc_2025_mains_gs2_q19")
            .expect("known GS-II foreign-policy question should be retrievable");
        assert_eq!(foreign_policy_question.main_tag, "International Relations");
        assert!(foreign_policy_question.subtags.iter().any(|subtag| {
            subtag == "Foreign Policy & Diplomacy" || subtag == "Bilateral Relations"
        }));

        let gs3_sections = vec!["mains-gs3".to_string()];
        let security = search_questions_cached(
            &conn,
            &search_index,
            "internal security intelligence investigative agencies",
            Some(&gs3_sections),
        )
        .unwrap();
        let security_question = security
            .results
            .iter()
            .find(|result| result.question_id == "upsc_2023_mains_gs3_q19")
            .expect("known GS-III internal-security question should be retrievable");
        assert_eq!(security_question.main_tag, "Internal Security");
        assert!(security_question.subtags.iter().any(|subtag| {
            subtag == "Security Forces, Agencies & Intelligence"
                || subtag == "Terrorism, Insurgency & Extremism"
        }));

        let cyber_security = search_questions_cached(
            &conn,
            &search_index,
            "cross-border cyber attacks",
            Some(&gs3_sections),
        )
        .unwrap();
        let cyber_security_question = cyber_security
            .results
            .iter()
            .find(|result| result.question_id == "upsc_2021_mains_gs3_q10")
            .expect("known GS-III cyber-security question should be retrievable");
        assert_eq!(cyber_security_question.main_tag, "Internal Security");
        assert!(cyber_security_question
            .subtags
            .iter()
            .any(|subtag| subtag == "Cyber Security & Communication Networks"));

        assert!(river.results.iter().any(|result| {
            let visible_text = format!(
                "{} {}",
                result.question,
                result
                    .options
                    .iter()
                    .map(|option| option.text.as_str())
                    .collect::<Vec<_>>()
                    .join(" ")
            )
            .to_lowercase();
            !visible_text.contains("river")
                && ["ocean", "sea", "marine", "coast"]
                    .iter()
                    .any(|concept| visible_text.contains(concept))
        }));

        for (query, related_terms) in [
            (
                "ocean",
                &["water", "river", "sea", "lake", "marine", "coast"][..],
            ),
            (
                "groundwater depletion",
                &["aquifer", "water scarcity", "irrigation", "well"][..],
            ),
            (
                "protecting forests from climate change",
                &["biodiversity", "ecosystem", "conservation", "wildlife"][..],
            ),
        ] {
            let related = search_questions_cached(&conn, &search_index, query, None).unwrap();
            assert!(!related.results.is_empty(), "no results for {query}");
            assert!(related
                .results
                .windows(2)
                .all(|pair| pair[0].similarity >= pair[1].similarity));
            assert!(
                related.results.iter().any(|result| {
                    let visible_text = format!(
                        "{} {}",
                        result.question,
                        result
                            .options
                            .iter()
                            .map(|option| option.text.as_str())
                            .collect::<Vec<_>>()
                            .join(" ")
                    )
                    .to_lowercase();
                    related_terms
                        .iter()
                        .any(|concept| visible_text.contains(concept))
                }),
                "no conceptually related result for {query}"
            );
        }
    }

    #[test]
    fn save_answer_rejects_completed_attempt() {
        // This test validates the TOCTOU transaction fix (#14):
        // Once an attempt is marked as 'completed', no further answers
        // should be accepted, even if the save_answer call happens
        // concurrently with submission.
        let mut conn = setup_conn();

        let bank_id = import_question_bank(&mut conn, &sample_bank()).unwrap();
        let attempt_id = crate::backend::db::attempt::create_test_attempt(
            &mut conn,
            &bank_id,
            crate::backend::types::TestMode::Test,
            None,
        )
        .unwrap();

        // Submit the test to move it to Completed.
        let questions =
            crate::backend::db::question_bank::fetch_questions_by_bank_id(&conn, &bank_id).unwrap();
        let responses =
            crate::backend::db::attempt::fetch_responses_by_attempt_id(&conn, &attempt_id).unwrap();
        let analysis = crate::backend::scoring::analyze_submission(
            &questions,
            &responses,
            &std::collections::HashMap::new(),
        );
        crate::backend::db::attempt::finalize_submission(
            &conn,
            &attempt_id,
            analysis.score,
            analysis.max_score,
            crate::backend::db::now_ms(),
        )
        .unwrap();

        // Now saving an answer should fail.
        let result = crate::backend::db::attempt::save_answer(
            &mut conn,
            &attempt_id,
            "q-1",
            Some(&serde_json::json!("a")),
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("not in progress"));
    }

    #[test]
    fn attempt_state_transitions_are_enforced() {
        let mut conn = setup_conn();
        let bank_id = import_question_bank(&mut conn, &sample_bank()).unwrap();
        let attempt_id = crate::backend::db::attempt::create_test_attempt(
            &mut conn,
            &bank_id,
            crate::backend::types::TestMode::Test,
            None,
        )
        .unwrap();

        crate::backend::db::attempt::pause_test(&conn, &attempt_id, 500).unwrap();
        assert!(crate::backend::db::attempt::pause_test(&conn, &attempt_id, 499).is_err());
        assert!(crate::backend::db::attempt::finalize_submission(
            &conn,
            &attempt_id,
            0.0,
            2.0,
            crate::backend::db::now_ms(),
        )
        .is_err());
        crate::backend::db::attempt::resume_test(&conn, &attempt_id).unwrap();
        crate::backend::db::attempt::finalize_submission(
            &conn,
            &attempt_id,
            0.0,
            2.0,
            crate::backend::db::now_ms(),
        )
        .unwrap();
        assert!(crate::backend::db::attempt::finalize_submission(
            &conn,
            &attempt_id,
            0.0,
            2.0,
            crate::backend::db::now_ms(),
        )
        .is_err());
        assert!(
            crate::backend::db::attempt::update_time_remaining(&conn, &attempt_id, 10).is_err()
        );
        assert!(crate::backend::db::attempt::toggle_flag(&conn, &attempt_id, "q-1").is_err());
    }

    #[test]
    fn invalid_duration_and_cross_bank_question_ids_are_rejected_cleanly() {
        let mut conn = setup_conn();
        let bank = sample_bank();
        let bank_id = import_question_bank(&mut conn, &bank).unwrap();
        assert!(crate::backend::db::attempt::create_test_attempt(
            &mut conn,
            &bank_id,
            crate::backend::types::TestMode::Test,
            Some(0),
        )
        .is_err());

        let conflicts =
            crate::backend::db::question_bank::question_id_conflicts(&conn, &bank).unwrap();
        assert_eq!(conflicts.len(), 1);
        assert!(conflicts[0].contains("questions[0].id"));
    }
}
