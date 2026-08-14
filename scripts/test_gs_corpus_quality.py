#!/usr/bin/env python3
"""Corpus integration test: every static/upsc mains-gs{1-4} bank must pass stem_issues.

This is the acceptance driver for GS data quality. Run from repo root or scripts/:

    python3 -m unittest scripts.test_gs_corpus_quality -v
    # or
    python3 scripts/test_gs_corpus_quality.py

Exit non-zero if any stem fails. Prints GS/year Qn:reasons for each failure.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Allow `python3 scripts/test_gs_corpus_quality.py` and unittest discovery
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from gs_quality_gate import check_paper, GS_FOLDERS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC = REPO_ROOT / "static" / "upsc"


def collect_failures(static_root: Path = STATIC) -> list[str]:
    failures: list[str] = []
    for gs, folder in GS_FOLDERS.items():
        d = static_root / folder
        if not d.is_dir():
            failures.append(f"MISSING_DIR {folder}")
            continue
        for path in sorted(d.glob("*.json")):
            if not path.stem.isdigit():
                continue
            year = int(path.stem)
            if year < 2013 or year > 2025:
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            qs = data.get("questions") or []
            issues = check_paper(gs, year, qs)
            for iss in issues:
                failures.append(f"{gs}/{year} {iss}")
    return failures


class TestGsCorpusQuality(unittest.TestCase):
    def test_all_gs_banks_pass_quality_gate(self):
        self.assertTrue(STATIC.is_dir(), f"missing static root {STATIC}")
        failures = collect_failures(STATIC)
        if failures:
            msg = (
                f"{len(failures)} quality defect(s) in GS corpus:\n"
                + "\n".join(f"  {f}" for f in failures[:200])
            )
            if len(failures) > 200:
                msg += f"\n  ... +{len(failures) - 200} more"
            self.fail(msg)


if __name__ == "__main__":
    fails = collect_failures()
    print(f"FAILURES {len(fails)}")
    for f in fails:
        print(f)
    if fails:
        raise SystemExit(1)
    print("ALL GS CORPUS PASS")
    raise SystemExit(0)
