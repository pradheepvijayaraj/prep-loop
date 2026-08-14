#!/usr/bin/env python3
"""Structural MCQ completeness for UPSC Prelims GS1 — inventory gate.

validate_mcq is a thin union of composable rules in scripts/prelims_rules/.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Ensure scripts/ is on path when run as script
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from prelims_rules import validate_mcq  # noqa: E402
from prelims_rules.numbered_stubs import is_stub_body, numbered_lines  # noqa: E402

# re-export
__all__ = [
    "validate_mcq",
    "inventory_prelims",
    "inventory_source_papers",
    "stem_fingerprint",
    "is_stub_body",
    "numbered_lines",
    "option_texts",
]


def option_texts(options: list | None) -> list[str]:
    out: list[str] = []
    for o in options or []:
        if isinstance(o, dict):
            out.append(str(o.get("text") or "").strip())
        else:
            out.append(str(o or "").strip())
    return out


def stem_fingerprint(stem: str) -> str:
    s = re.sub(r"\s+", " ", (stem or "").lower())
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    # The opening words of many UPSC stems are deliberately generic (for
    # example, "Consider the following statements").  Comparing the complete
    # normalised stem catches real duplicates without falsely flagging them.
    return s


def inventory_prelims(bank_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_year_fps: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for f in sorted(Path(bank_dir).glob("*.json")):
        data = json.loads(f.read_text())
        qs = data.get("questions") or []
        for i, q in enumerate(qs):
            stem = q.get("question") or q.get("stem") or ""
            opts = q.get("options") or []
            reasons = validate_mcq(stem, opts)
            ans = q.get("correctAnswers") or (q.get("answer") or {}).get("correct") or []
            if not ans:
                reasons.append("missing_answer")
            num = i + 1
            if reasons:
                rows.append(
                    {
                        "year": f.stem,
                        "num": num,
                        "id": q.get("id"),
                        "reasons": reasons,
                        "stem_preview": stem[:160].replace("\n", " | "),
                    }
                )
            fp = stem_fingerprint(stem)
            if len(fp) > 50:
                by_year_fps[f.stem][fp].append(num)

    for year, fps in by_year_fps.items():
        for fp, nums in fps.items():
            if len(nums) >= 2:
                for n in nums[1:]:
                    rows.append(
                        {
                            "year": year,
                            "num": n,
                            "id": f"dup_{year}_{n}",
                            "reasons": ["duplicate_stem"],
                            "stem_preview": fp[:100],
                            "dup_of": nums[0],
                        }
                    )
    rows.sort(key=lambda r: (r["year"], int(r["num"])))
    return rows


def inventory_source_papers(src_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year_dir in sorted(Path(src_root).glob("*")):
        pj = year_dir / "paper.json"
        if not pj.exists():
            continue
        year = year_dir.name
        data = json.loads(pj.read_text())
        fps: dict[str, list[int]] = defaultdict(list)
        for q in data.get("questions") or []:
            stem = q.get("question") or ""
            opts = q.get("options") or []
            num = int(q.get("number") or 0)
            reasons = validate_mcq(stem, opts)
            ans = (q.get("answer") or {}).get("correct") or []
            if not ans:
                reasons.append("missing_answer")
            if reasons:
                rows.append(
                    {
                        "year": year,
                        "num": num,
                        "reasons": reasons,
                        "stem_preview": stem[:160].replace("\n", " | "),
                    }
                )
            fp = stem_fingerprint(stem)
            if len(fp) > 50:
                fps[fp].append(num)
        for fp, nums in fps.items():
            if len(nums) >= 2:
                for n in nums[1:]:
                    rows.append(
                        {
                            "year": year,
                            "num": n,
                            "reasons": ["duplicate_stem"],
                            "stem_preview": fp[:100],
                            "dup_of": nums[0],
                        }
                    )
    rows.sort(key=lambda r: (r["year"], int(r["num"])))
    return rows


if __name__ == "__main__":
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("static/upsc/prelims-gs1")
    inv = inventory_prelims(d)
    print(f"INVENTORY_COUNT={len(inv)}")
    by_year: dict[str, int] = defaultdict(int)
    for r in inv:
        by_year[r["year"]] += 1
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]}")
    for r in inv[:40]:
        print(f"  {r['year']} Q{r['num']} {r['reasons']}: {r['stem_preview'][:90]}")
    if len(inv) > 40:
        print(f"  ... +{len(inv) - 40}")
    sys.exit(0 if not inv else 1)
