#!/usr/bin/env python3
"""Regression tests for booklet multi-Q OCR module using real bank snippets."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from gs_booklet import booklet_stem_issues, split_booklet_stem  # noqa: E402
from gs_quality_gate import stem_issues  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
STATIC = REPO / "static" / "upsc"


def _load(folder: str, year: int, qn: int) -> str:
    path = STATIC / folder / f"{year}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["questions"][qn - 1]["question"]


class TestBookletRealBanks(unittest.TestCase):
    """These must fail the gate if multi-Q booklet soup is reintroduced."""

    def test_gs2_2013_q3_multi_word_limit_merge(self):
        # Historical multi-merge pattern (may be fixed in banks — still assert module catches soup)
        soup = (
            "'The Supreme Court of India keeps a check on arbitrary power of the Parliament "
            "in amending the Constitution.' Discuss critically. [200 words] 10 Many State "
            "Governments further bifurcate geographical administrative areas like Districts "
            "and Talukas for better governance. In light of the above, can it also be "
            "justified that more number of smaller States would bring in effective "
            "governance? [200 words] 10 The product diversification of financial "
            "institutions has made regulation an increasing challenge. Discuss. [200 words]"
        )
        bi = booklet_stem_issues(soup, 3)
        self.assertTrue(any("multi_word_limit" in i or "mid_mark_merge" in i for i in bi), bi)
        fi = stem_issues(soup, 3)
        self.assertTrue(len(fi) > 0, fi)

    def test_gs2_2013_q7_orphan_word_limit(self):
        soup = "Examine in light of the fact that India is faced with a [200 words]"
        bi = booklet_stem_issues(soup, 7)
        self.assertTrue(any("orphan_word_limit" in i for i in bi), bi)
        self.assertTrue(stem_issues(soup, 7))

    def test_gs2_2013_q10_bang_opener(self):
        soup = (
            "! split in society between the nationalists and Islamic forces. "
            "What is its significance for India? [200 words]"
        )
        bi = booklet_stem_issues(soup, 10)
        self.assertTrue(
            any("bang" in i or "split_opener" in i for i in bi),
            bi,
        )
        self.assertTrue(stem_issues(soup, 10))

    def test_gs1_2023_triple_merge_topic_shift(self):
        soup = (
            "Do you think marriage as a sacrament is losing its value in modern India? "
            "Child cuddling is now being replaced by mobile phones. Discuss its impact "
            "on the socialization of children. Why is caste identity in India both "
            "fluid and static?"
        )
        bi = booklet_stem_issues(soup, 19)
        self.assertTrue(any("topic_shift" in i for i in bi), bi)
        self.assertTrue(stem_issues(soup, 19))

    def test_live_gs2_2013_stems_clean_after_rebuild(self):
        """Shipped bank must not reintroduce booklet soup on skeptic Qs."""
        if not (STATIC / "mains-gs2" / "2013.json").exists():
            self.skipTest("bank missing")
        for qn in (3, 7, 10):
            stem = _load("mains-gs2", 2013, qn)
            self.assertEqual(
                booklet_stem_issues(stem, qn),
                [],
                f"Q{qn} still has booklet issues: {stem[:120]!r}",
            )
            self.assertEqual(stem_issues(stem, qn), [], f"Q{qn} full gate: {stem[:120]!r}")

    def test_live_gs1_2023_q19_not_triple_merge(self):
        if not (STATIC / "mains-gs1" / "2023.json").exists():
            self.skipTest("bank missing")
        stem = _load("mains-gs1", 2023, 19)
        self.assertEqual(booklet_stem_issues(stem, 19), [])
        self.assertNotIn("Child cuddling", stem)
        self.assertEqual(stem_issues(stem, 19), [])

    def test_split_booklet_stem_extracts_units(self):
        soup = (
            "Discuss Section 66A of the IT Act. [200 words] 10 Many State Governments "
            "further bifurcate districts for better governance. Discuss. [200 words]"
        )
        units = split_booklet_stem(soup)
        self.assertGreaterEqual(len(units), 2)
        self.assertTrue(any("66A" in u or "Section" in u for u in units))

    def test_legit_multipart_not_flagged(self):
        s = (
            "What are Tsunamis? How and where are they formed? What are their "
            "consequences? Explain with examples."
        )
        self.assertEqual(booklet_stem_issues(s, 7), [])


if __name__ == "__main__":
    unittest.main()
