#!/usr/bin/env python3
"""Unit tests for GS quality-gate predicates (no network)."""

from __future__ import annotations

import unittest

from gs_quality_gate import check_paper, stem_issues, min_count, expected_marks


class TestStemIssues(unittest.TestCase):
    def test_clean_stem_ok(self):
        s = "Discuss the salient features of the Harappan architecture in detail."
        self.assertEqual(stem_issues(s, 1), [])

    def test_quote_start_ok(self):
        s = (
            '"Access to affordable energy is essential for development." '
            "Comment on India's progress in this regard with examples."
        )
        self.assertEqual(stem_issues(s, 1), [])

    def test_egovernance_ok(self):
        s = (
            "e-governance projects have a built-in bias towards technology "
            "and back-end integration than user-centric designs. Examine."
        )
        self.assertEqual(stem_issues(s, 1), [])

    def test_short_stem(self):
        self.assertTrue(any("short" in i for i in stem_issues("Too short.", 1)))

    def test_devanagari(self):
        s = "भारत Discuss the role of the President of India in detail here."
        self.assertTrue(any("devanagari" in i for i in stem_issues(s, 2)))

    def test_glued_marks(self):
        s = "Discuss the causes of the revolt of 1857 in India10"
        self.assertTrue(any("glued_marks" in i for i in stem_issues(s, 3)))

    def test_ocr_marks_12vi(self):
        s = (
            "How can the Digital India programme help farmers to improve "
            "farm productivity and income in India? 12Vi"
        )
        self.assertTrue(any("glued_marks" in i for i in stem_issues(s, 1)))

    def test_broken_tail_ai(self):
        s = "Evaluate the role of the Self Help Groups in ai)"
        issues = stem_issues(s, 13)
        self.assertTrue(
            any("broken_tail" in i or "truncated" in i for i in issues),
            issues,
        )

    def test_orphan_elucidate(self):
        s = "Critically elucidate the statement. (200 words]"
        issues = stem_issues(s, 19)
        self.assertTrue(
            any("orphan" in i or "header_bleed" in i for i in issues),
            issues,
        )

    def test_section_bleed(self):
        s = "Justify with suitable illustration. SECTION B"
        issues = stem_issues(s, 6)
        self.assertTrue(
            any("header_bleed" in i or "orphan" in i for i in issues),
            issues,
        )

    def test_answer_in_words_bleed(self):
        s = (
            "The incidence and intensity of poverty are more important in "
            "determining poverty Multidimensional Poverty Index Report. "
            "(Answer in 250 words)"
        )
        issues = stem_issues(s, 12)
        self.assertTrue(
            any(
                "header_bleed" in i or "broken_clause" in i or "truncated" in i
                for i in issues
            ),
            issues,
        )

    def test_latinized_ocr_mashup(self):
        s = (
            "A mere compliance with law is not enough f^WffacTT ^TfR-TTfrf) "
            "% W * ^ftfcT and more text here about public service ethics."
        )
        issues = stem_issues(s, 3)
        self.assertTrue(
            any(
                "garble" in i or "ocr_symbols" in i or "low_english" in i
                for i in issues
            ),
            issues,
        )

    def test_merged_q_marker(self):
        s = (
            "Discuss land reforms in India. (200 words] 10 Q. 9( a) Discuss "
            "the impact of FDI entry into Multi-trade retail sector."
        )
        issues = stem_issues(s, 20)
        self.assertTrue(any("merged_q" in i for i in issues), issues)

    def test_header_bleed(self):
        s = (
            "Discuss the role of the Finance Commission in India. "
            "10 General Studies Paper 2"
        )
        self.assertTrue(any("header_bleed" in i for i in stem_issues(s, 5)))

    def test_trailing_n_mark(self):
        s = "Describe the characteristics and type of primary rocks. 10 mark"
        self.assertTrue(any("glued_marks" in i for i in stem_issues(s, 4)))

    def test_gs_question_paper_footer(self):
        s = (
            "Enumerate the changes taking place in Indian society. "
            "15 GS1 Question Paper"
        )
        self.assertTrue(any("header_bleed" in i for i in stem_issues(s, 20)))

    def test_by_guillemet_tail(self):
        s = (
            "Discuss the food processing industries of North-West India. 10 by«"
        )
        issues = stem_issues(s, 6)
        self.assertTrue(
            any("truncated" in i or "glued_marks" in i for i in issues),
            issues,
        )

    def test_act_trunc_tail(self):
        s = (
            "Comment on the National Judicial Appointments Commission Act,"
        )
        self.assertTrue(any("truncated" in i for i in stem_issues(s, 18)))

    def test_skyc_booklet_code(self):
        s = (
            "How does social capital enhance good governance? 10 SKYC-G-GSF"
        )
        issues = stem_issues(s, 5)
        self.assertTrue(
            any("booklet_code" in i or "glued_marks" in i for i in issues),
            issues,
        )

    def test_plus_marks_tail(self):
        s = (
            "What are the main functions of the United Nations Economic and Social 5+5"
        )
        self.assertTrue(any("truncated" in i for i in stem_issues(s, 10)))

    def test_bare_suggest_trunc(self):
        s = (
            "Explain how narco-terrorism has emerged as a serious threat "
            "across the country. Suggest"
        )
        self.assertTrue(any("truncated" in i for i in stem_issues(s, 9)))

    def test_title_noun_trunc(self):
        s = (
            "Mention the important components of the National Landslide Risk Management"
        )
        self.assertTrue(any("truncated" in i for i in stem_issues(s, 18)))

    def test_section_dash_b(self):
        s = (
            "Examine gender-specific challenges faced by female public servants. "
            "SECTION - B"
        )
        self.assertTrue(any("header_bleed" in i for i in stem_issues(s, 5)))

    def test_ocr_soup_taken20(self):
        s = (
            "What are the extra precautionary measures to be taken20 os, r 7 a - ;"
        )
        self.assertTrue(any("ocr_soup" in i for i in stem_issues(s, 10)))

    def test_lone_pipe_ocr(self):
        s = (
            "There has been increasing concern to develop effective | internalizing "
            "integrity and ethics in the civil services."
        )
        self.assertTrue(any("lone_pipe" in i for i in stem_issues(s, 1)))

    def test_topic_label_bleed(self):
        s = (
            "The Supreme Court keeps a check on arbitrary power of Parliament. "
            "Comparison of Constitution"
        )
        self.assertTrue(any("topic_label" in i for i in stem_issues(s, 16)))

    def test_nonsense_causes_of_india(self):
        s = (
            "Flooding in urban areas is an emerging climate-induced disaster. "
            "Discuss the causes of India. Describe the policies and frameworks."
        )
        self.assertTrue(any("nonsense" in i for i in stem_issues(s, 18)))

    def test_incomplete_risk_reduction_framework(self):
        s = (
            "What is disaster resilience? How is it determined? "
            "Describe various elements of a Risk Reduction (2015-2030)."
        )
        self.assertTrue(any("incomplete_framework" in i for i in stem_issues(s, 17)))

    def test_near_dup_stems_in_paper(self):
        qs = [
            {
                "question": (
                    "What is the present world scenario of intellectual property "
                    "rights with respect to life materials? Although India is second "
                    "in the world to file patents, still only a few have been commercialized."
                ),
                "marks": 10,
            },
            {
                "question": (
                    "What is the present world scenario of intellectual property "
                    "rights with respect to life materials? Discuss with examples."
                ),
                "marks": 15,
            },
        ]
        # pad to min count
        while len(qs) < 20:
            qs.append(
                {
                    "question": (
                        f"Discuss unique developmental policy question number {len(qs)+1} "
                        f"about Indian economy with suitable examples?"
                    ),
                    "marks": 10 if len(qs) < 10 else 15,
                }
            )
        issues = check_paper("GS3", 2024, qs)
        self.assertTrue(any("near_dup" in i for i in issues), issues)


class TestPaperRules(unittest.TestCase):
    def test_min_count_gs4(self):
        self.assertEqual(min_count("GS4", 2020), 10)

    def test_min_count_gs1(self):
        self.assertEqual(min_count("GS1", 2020), 19)
        self.assertEqual(min_count("GS1", 2013), 20)

    def test_expected_marks_modern(self):
        self.assertEqual(expected_marks("GS1", 2022, 1, 20), 10.0)
        self.assertEqual(expected_marks("GS1", 2022, 11, 20), 15.0)

    def test_expected_marks_older(self):
        self.assertEqual(expected_marks("GS1", 2015, 1, 20), 12.5)

    def test_check_paper_thin(self):
        qs = [{"question": "x" * 50, "marks": 10} for _ in range(5)]
        issues = check_paper("GS1", 2020, qs)
        self.assertTrue(any(i.startswith("count=") for i in issues))

    def test_check_paper_full_clean(self):
        qs = []
        for i in range(1, 21):
            qs.append(
                {
                    "question": (
                        f"Discuss question number {i} about Indian polity "
                        f"and society in detail with suitable examples?"
                    ),
                    "marks": 10.0 if i <= 10 else 15.0,
                }
            )
        self.assertEqual(check_paper("GS2", 2022, qs), [])


if __name__ == "__main__":
    unittest.main()
