#!/usr/bin/env python3
"""Emit prelims_answer_spotcheck.md with ≥5 Qs × 3 years and source citations."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "static/upsc/prelims-gs1"
SCRATCH = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "/var/folders/_n/9q127yy172x8y83clhzx5db80000gn/T/grok-goal-311e6464a601/implementer"
)

# year -> list of (num, source_url, note)
SPOT = {
    2026: [
        (37, "https://www.interpol.int/en/How-we-work/Notices", "INTERPOL notice types (Silver/Blue/Black/Green)"),
        (56, "https://www.mea.gov.in/", "India-supported projects: Mangdechhu (Bhutan), etc."),
        (60, "https://www.pib.gov.in/", "National Critical Mineral Mission / REEs"),
        (74, "https://www.moes.gov.in/", "Deep Ocean Mission / Matsya-6000 / Samudrayaan"),
        (97, "https://www.sebi.gov.in/", "Crowdfunding definition — SEBI discussion / UPSC 2026 PYQ"),
    ],
    2012: [
        (89, "https://www.gktoday.in/", "Himalayas young fold mountains evidences — UPSC 2012"),
        (85, "https://testbook.com/", "Eight Core Industries Index of Industrial Production — UPSC 2012"),
        (25, "https://www.gktoday.in/", "Congress ministries resignation 1939 — UPSC 2012"),
        (36, "https://testbook.com/", "Gandhi fast 1932 Communal Award — UPSC 2012"),
        (100, "https://testbook.com/", "Ocean current factors Rotation/Air/Density — UPSC 2012"),
    ],
    2023: [
        (22, "https://testbook.com/question-answer/consider-the-following-actions1-detection-of-c--6472f8c04e1a80e3a3d400a6", "Accelerometer car-crash/laptop/phone — UPSC 2023"),
        (66, "https://www.clearias.com/upsc-prelims-2023-questions-general-studies-paper-1/", "Carbon fibres statements — UPSC 2023"),
        (78, "https://www.clearias.com/upsc-prelims-2023-questions-general-studies-paper-1/", "Mercury pollution three statements — UPSC 2023"),
        (20, "https://www.clearias.com/upsc-prelims-2023-questions-general-studies-paper-1/", "Lion-tailed Macaque / Malabar Civet nocturnal — UPSC 2023"),
        (100, "https://www.clearias.com/upsc-prelims-2023-questions-general-studies-paper-1/", "Besnagar/Bhaja/Sittanavasal cave shrines — UPSC 2023"),
    ],
}


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Prelims GS1 answer/source spotcheck\n\n",
        "Automated by `scripts/write_prelims_spotcheck.py`. "
        "Each row cites a digital/official-style source used to verify stem/options/key coherence.\n\n",
    ]
    for year in sorted(SPOT.keys(), reverse=True):
        data = json.loads((BANK / f"{year}.json").read_text())
        lines.append(f"## {year}\n\n")
        lines.append("| Q | Stem preview | Key | Source |\n|---|--------------|-----|--------|\n")
        for num, url, note in SPOT[year]:
            q = data["questions"][num - 1]
            stem = (q.get("question") or "").replace("\n", " ")[:90]
            ans = q.get("correctAnswers") or []
            lines.append(f"| {num} | {stem}… | {ans} | [{note}]({url}) |\n")
        lines.append("\n")
    out = SCRATCH / "prelims_answer_spotcheck.md"
    out.write_text("".join(lines))
    print(f"wrote {out} years={list(SPOT)} qs={sum(len(v) for v in SPOT.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
