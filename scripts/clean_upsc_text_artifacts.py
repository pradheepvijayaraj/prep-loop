#!/usr/bin/env python3
"""Remove unambiguous scan headers and pagination debris from bundled UPSC JSON.

This deliberately does not rewrite question language or map content. Those need
source-by-source verification rather than an automated guess.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# Examples: CRNA-F-HST/15 3 [P.T.O.], PHKM-U-GEG/26 6, M-ESE-U-GPY 4.
PAGE_CODE = re.compile(
    r"(?:\s|^)(?:[A-Z]{1,5}-){2,5}[A-Z]{2,5}(?:/\d+)?\s+\d+"
    r"(?:\s*\[\s*P\.?\s*T\.?\s*[O0]\.?\s*\])?"
)
# Restrict this to a standalone marker.  Without word boundaries it can match
# ordinary text such as "help to", causing a destructive false cleanup.
PTO = re.compile(r"(?<!\w)\[?\s*P\.?\s*T\.?\s*[O0]\.?\s*\]?(?!\w)", re.I)
ROLL_NUMBER = re.compile(r"(?mi)^\s*DO NOT WRITE YOUR ROLL NO\. ON THIS SHEET\s*$")
# OCR occasionally leaves a standalone all-capital page code, for example
# ``CRNA-F-PBAD - 6``.  This is deliberately case-sensitive so ordinary
# hyphenated question language is never removed.
PAGE_CODE_LINE = re.compile(r"(?m)^.*(?:[A-Z]{1,5}[-—]){2,}[A-Z]{1,5}.*$")


def clean(text: str) -> str:
    value = PAGE_CODE.sub("\n", text or "")
    value = PTO.sub("", value)
    value = ROLL_NUMBER.sub("", value)
    value = PAGE_CODE_LINE.sub("", value)
    # Map scans are not usable as question text. Where a clean textual prompt
    # precedes the scan, keep that prompt and discard only the image OCR tail.
    map_start = re.search(r"(?im)^.*\(map_[^)]*\).*$", value)
    if map_start and len(value[: map_start.start()].strip()) >= 80:
        value = value[: map_start.start()]
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("root", nargs="?", type=Path, default=Path("static/upsc"))
    args = parser.parse_args()

    changed_files = 0
    changed_questions = 0
    for path in sorted(args.root.glob("**/*.json")):
        if path.name == "catalog.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for question in data.get("questions") or []:
            original = str(question.get("question") or "")
            revised = clean(original)
            if revised != original:
                changed = True
                changed_questions += 1
                if args.write:
                    question["question"] = revised
        if changed:
            changed_files += 1
            if args.write:
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"changed_files={changed_files} changed_questions={changed_questions} write={args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
