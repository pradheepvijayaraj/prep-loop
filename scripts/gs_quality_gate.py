#!/usr/bin/env python3
"""Quality gate for UPSC Mains GS1–GS4 banks under static/upsc.

Fails (exit 1) if any paper violates count / coherent-English stem rules.
Predicates are structural (not year-specific prefix allowlists) so they catch
new OCR failures: truncated tails, orphan fragments, section bleed, latinized
Hindi mashups, booklet codes, and glued marks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from gs_booklet import booklet_stem_issues  # structural multi-Q booklet OCR

# --- structural patterns ---

DEVANAGARI = re.compile(r"[\u0900-\u097F]")

# Glued / OCR-mangled trailing marks (India10, 12Vi, "10 mark", "15 marks")
GLUED_MARKS = re.compile(
    r"(?:"
    r"[A-Za-z](?:10|12\.5|15|20)\.?$"
    r"|12\s*[Vv][iI1!l]"
    r"|12\s*[—\-–%]"
    r"|\b12\s*—\s*\d*"
    r"|\b(?:10|12\.5|15|20)\s*marks?\s*$"
    r"|\b(?:10|12\.5|15|20)\s*mark\s*$"
    r")",
    re.I,
)

# Known garble tokens + latinized-Hindi OCR mashups (no Devanagari codepoints)
GARBLE_TOKENS = re.compile(
    r"(?:"
    r"\b(frou|fenfea|Framra|viata|soreaat|mara we|pra om|ciein eafags|incedence)\b"
    r"|f\^W|3t\s*r\s*\^|e-\(FD|3\?K|\}fd=|chdl\.|f\^T|TTfrf|FT2\s*\{"
    r"|1Rl!|1J\(ll|<\s*!\s*\\\\"
    r")",
    re.I,
)

HEADER_BLEED = re.compile(
    r"(?:"
    r"General Studies Paper|QCA Booklet|UPSC MAINS\s+\d{4}\s*\|"
    r"|Please read each of the following instructions"
    r"|There are TWENTY questions printed"
    r"|\bSECTION\s*[-–—]?\s*[A-D]\b"
    r"|\bAnswer in\s+\d+\.?\s*words?\b"
    r"|\(\s*Answer in\s+\d+"
    r"|\bGS[1-4]\s+Question\s+Paper\b"
    r")"
    # bare "(200 words]" / mismatched brackets only when mid-stem garbage,
    # not a clean trailing "(200 words)" which we strip at rebuild time
    r"|(?:\(\s*\d{2,3}\s*words?\s*\]|\[\s*\d{2,3}\s*words?\s*\))",
    re.I,
)

BOOKLET_CODE = re.compile(
    r"(?:"
    r"ibU-|SB\d+[—\-]|BS\d+[—\-]|4\s*SB\d+|CADRN|STHED|>ibU"
    r"|SKYC-G-GSF|SKYC-[A-Z]-GSF|PHKM-B-MTH|HXS-G-GSF|CRNA-X-GSF"
    r")",
    re.I,
)

BRACE_JUNK = re.compile(r"\{[)\]\}]\s*$")
BAD_PUNCT_START = re.compile(r"^[,;.)\]}~`|]+")

# Truncated / incomplete endings (structural)
TRUNC_END = re.compile(
    r"(?:"
    # hanging function words / incomplete clause openers at end
    r"\b(?:the|a|an|of|to|in|and|or|for|with|from|on|at|by|as|that|which|its|their|this|these|those"
    r"|be|been|being|is|are|was|were|have|has|had|do|does|did|will|would|can|could|should|may|might"
    r"|important to be|how does it|all the more|for ensuring|would you|etc\.\s*Under|posting etc)\s*$"
    # bare imperative cut mid-prompt
    r"|\b(?:Suggest|Examine|Discuss|Explain|Describe|Analyse|Analyze|Evaluate|Elucidate|Comment|Highlight|Enumerate)\s*$"
    # title-style noun phrase cut (no terminal punct): "... Risk Management" / "... Cyber Security"
    r"|\b(?:Risk Management|Cyber Security|Border Area Development|multilayered|excellent intelligence"
    r"|guidance in public|National Landslide Risk Management|National Cyber Security)\s*$"
    # OCR mark fragments at end
    r"|\s+12\s*[Vv—\-–%iI1l].*$"
    r"|\s+12\.?\s*$"
    # broken tail like "in ai)" / "in ai"
    r"|\bin\s+ai\)?\s*$"
    r"|\bai\)\s*$"
    # mid-title cut: "… Commission Act,"
    r"|Act,\s*$"
    # OCR guillemet / plus-marks tails
    r"|by[«»]\s*$"
    r"|\d\+\d=?\s*$"
    r"|\b105\s*:\s*$"
    # ends with dangling dash/ellipsis garbage (not a normal period/question)
    r"|[—–~^@#*|\\«»]\s*$"
    r")",
    re.I,
)

# OCR soup tails: glued marks + noise letters "...taken20 os, r 7 a - ;"
OCR_SOUP_TAIL = re.compile(
    r"(?:"
    r"[A-Za-z]{3,}\d{2,}\s+[a-z]{1,3}\s*,"
    r"|taken\d+\s+os\b"
    r"|\bos,\s*r\s+\d+\s+a\b"
    r")",
    re.I,
)

# Syllabus/topic-label bleed appended after a real stem
TOPIC_LABEL_BLEED = re.compile(
    r"(?:"
    r"\.\s*Comparison of Constitution\s*$"
    r"|\.\s*Government policies and interventions\s*$"
    r"|\.\s*Development processes and the development industry\s*$"
    r"|\.\s*Development processes\b.*$"
    r"|\bComparison of Constitution\s*$"
    r"|\bGovernment policies and interventions\s*$"
    r")",
    re.I,
)

# Nonsensical complete-sentence OCR / cut-paste (ends with punct but is wrong English)
NONSENSE_PHRASE = re.compile(
    r"(?:"
    r"\bcauses of India\b"
    r"|\beffects of India\b"
    r"|\bcauses of the India\b"
    r"|\brole of India\.\s"
    r"|\bDiscuss the causes of India\b"
    r")",
    re.I,
)

# Incomplete framework / programme titles (even when punctuated)
INCOMPLETE_FRAMEWORK = re.compile(
    r"(?:"
    r"\belements of a Risk Reduction\b"
    r"|\ba Risk Reduction\s*\(\s*2015"
    r"|\bSendai\s*$"
    r"|\bFramework for Disaster\s*$"
    r"|\bvarious elements of a Risk\b"
    r")",
    re.I,
)

# Orphan / incomplete prompt fragments (must be the WHOLE stem, or explicit fragment)
ORPHAN_PROMPT = re.compile(
    r"(?is)^(?:"
    # entire stem is just a bare imperative / meta-instruction
    r"(?:Critically\s+)?(?:elucidate|examine|discuss|explain|comment|justify|evaluate)"
    r"(?:\s+the\s+statement)?\.?\s*"
    r"(?:\(\s*\d{2,3}\s*words?\s*[\]\)]|\(\s*Answer in[^)]*\)|SECTION\s+[A-D])?\s*$"
    # explicit incomplete fragments seen in OCR dumps
    r"|Justify with suitable illustration\.?\s*(?:SECTION\s+[A-D])?\s*$"
    r"|What is its significance for India and what steps are required to be taken to control this menace\s*\??"
    r"(?:\s*\[\s*\d{2,3}\s*words?\s*[\]\)])?\s*$"
    r"|Critically evaluate with a suitable example\.?\s*b\).*$"
    r"|How to build a suitable attitude needed for a public servant\?.*$"
    r")"
)

# Mid-stem mark bleed: "... 10 Explain the term..."
MID_MARK_BLEED = re.compile(
    r"(?<=\S)\s+(?:10|12\.5|15|20)\s+"
    r"(?:Explain|Discuss|Examine|What|How|Why|Describe|Analyse|Analyze|Comment|Elucidate|Evaluate)\b",
    re.I,
)
# Budget/OCR fragment starts: "18 is to 'transform..."
DIGIT_FRAGMENT_START = re.compile(r"^\d{1,2}\s+is\s+to\b", re.I)
# Incomplete mid-thought openers from split OCR
MID_OPEN_FRAGMENT = re.compile(
    r"^(?:ive reasons\.|India['’]\.\s*Analyse|What are the other factors available for growth potential\s*\?\s*$)",
    re.I,
)

# Multi-question OCR merge markers inside one stem
MERGED_Q_MARK = re.compile(
    r"(?:"
    r"\bQ\.\s*\d+\s*[\(\)]"
    r"|\bQ\.\s*\d+\s*[a-z]\)"
    r"|\b10\s+Q\.\s*\d+"
    r"|\b5\s+1J"
    r")",
    re.I,
)

# High-noise OCR: many non-alphanumeric odd symbols in a short stem
OCR_SYMBOLS = re.compile(r"[~^#@*\\<>]{2,}|\d+m\s+W|=\s*12|7T\+|3#T|\^[A-Za-z]{2,}")

# Common English openers for UPSC stems (allowlist for lower_start exception only)
LEGIT_LOWER_OPEN = re.compile(r"^(?:e-|[a-z]\)\s|[a-z]\.\s|“|\"|'|‘)")

# High-frequency English words for "is this actually English?" scoring
_COMMON = set(
    """
    the of and to in a is that for on with as by from are this be or an it was at
    which have has been were will would can could should may might not their its
    they them these those than then into also such more most only over under between
    about after before during against without within through while where when what
    who how why all any each both few other some many much same so if because discuss
    examine analyse analyze comment critically evaluate explain describe assess
    highlight reasons impact role significance india indian government policy
    constitution society economic social political culture history geography answer
    words marks question section following given above below account nature present
    consider define using state write public service ethics integrity corruption
    development security agriculture industry technology environment climate
    """.split()
)

GS_FOLDERS = {
    "GS1": "mains-gs1",
    "GS2": "mains-gs2",
    "GS3": "mains-gs3",
    "GS4": "mains-gs4",
}


def min_count(gs: str, year: int) -> int:
    if gs == "GS4":
        return 10
    return 20 if year == 2013 else 19


def expected_marks(gs: str, year: int, q_index: int, total: int) -> float | None:
    if gs == "GS4":
        return None
    if year <= 2016:
        return 12.5
    if total >= 20:
        return 10.0 if q_index <= 10 else 15.0
    return None


def _english_word_ratio(s: str) -> float:
    words = re.findall(r"[A-Za-z']+", s.lower())
    if len(words) < 6:
        return 1.0  # too short — handled by short-stem rule
    hits = sum(1 for w in words if w in _COMMON)
    return hits / len(words)


def _odd_char_ratio(s: str) -> float:
    if not s:
        return 0.0
    odd = sum(
        1
        for c in s
        if not c.isalnum()
        and c not in " \n\t.,;:?!\"'“”‘’()-–—/&%[]"
    )
    return odd / max(1, len(s))


def stem_issues(stem: str, qnum: int) -> list[str]:
    s = (stem or "").strip()
    issues: list[str] = []

    # Structural multi-question booklet merges (shared module)
    issues.extend(booklet_stem_issues(s, qnum))

    if len(s) < 40:
        issues.append(f"Q{qnum}:short({len(s)})")

    if DEVANAGARI.search(s):
        issues.append(f"Q{qnum}:devanagari")

    if GLUED_MARKS.search(s):
        issues.append(f"Q{qnum}:glued_marks")

    if GARBLE_TOKENS.search(s):
        issues.append(f"Q{qnum}:garble_token")

    if HEADER_BLEED.search(s):
        issues.append(f"Q{qnum}:header_bleed")

    if TOPIC_LABEL_BLEED.search(s):
        issues.append(f"Q{qnum}:topic_label_bleed")

    if NONSENSE_PHRASE.search(s):
        issues.append(f"Q{qnum}:nonsense_phrase")

    if INCOMPLETE_FRAMEWORK.search(s):
        issues.append(f"Q{qnum}:incomplete_framework")

    if OCR_SOUP_TAIL.search(s):
        issues.append(f"Q{qnum}:ocr_soup_tail")
    # mid-stem OCR pipe separators / junk tokens
    if re.search(r"\s\|\s", s) or re.search(r"\bureat\b", s, re.I):
        issues.append(f"Q{qnum}:lone_pipe_ocr")

    if BOOKLET_CODE.search(s):
        issues.append(f"Q{qnum}:booklet_code")

    if BRACE_JUNK.search(s):
        issues.append(f"Q{qnum}:brace_junk")

    if BAD_PUNCT_START.match(s):
        issues.append(f"Q{qnum}:punct_start")

    if ORPHAN_PROMPT.match(s):
        issues.append(f"Q{qnum}:orphan_prompt")

    if MERGED_Q_MARK.search(s):
        issues.append(f"Q{qnum}:merged_q_marker")

    # lowercase continuation (not e-governance / subpart / quote)
    if re.match(r"^[a-z]", s) and not LEGIT_LOWER_OPEN.match(s):
        issues.append(f"Q{qnum}:lower_start")

    # Truncated / broken endings (include long cases cut mid-clause)
    if TRUNC_END.search(s):
        # Allow clean endings that end with normal sentence punctuation
        if not re.search(r"[?\.!\"”’']\s*$", s):
            issues.append(f"Q{qnum}:truncated_end")

    if MID_MARK_BLEED.search(s):
        issues.append(f"Q{qnum}:mid_mark_bleed")
    if DIGIT_FRAGMENT_START.match(s):
        issues.append(f"Q{qnum}:digit_fragment_start")
    if MID_OPEN_FRAGMENT.match(s):
        issues.append(f"Q{qnum}:mid_open_fragment")

    # Explicit broken OCR tails the skeptic found
    if re.search(r"\bin\s+ai\)?\s*$", s, re.I) or re.search(r"\bai\)\s*$", s, re.I):
        issues.append(f"Q{qnum}:broken_tail")

    if OCR_SYMBOLS.search(s) or _odd_char_ratio(s) > 0.06:
        # Long clean cases can have some punctuation; only flag when noisy
        if _odd_char_ratio(s) > 0.06 or OCR_SYMBOLS.search(s):
            issues.append(f"Q{qnum}:ocr_symbols")

    # Trailing bare marks after sentence end
    if re.search(r"(?<=[.\"'?])\s*(?:10|12\.5|15|20|12Vi|12V)\s*$", s, re.I):
        issues.append(f"Q{qnum}:trailing_marks")

    # Low common-word ratio → latinized OCR English-looking garbage.
    # Threshold kept low so proper-noun-heavy clean stems still pass.
    ratio = _english_word_ratio(s)
    if len(re.findall(r"[A-Za-z']+", s)) >= 14 and ratio < 0.12:
        issues.append(f"Q{qnum}:low_english_ratio({ratio:.2f})")

    # Specific known OCR-broken clause (missing words before Multidimensional)
    if re.search(r"(?i)determining poverty\s+Multidimensional\s+Poverty\s+Index\s+Report", s):
        issues.append(f"Q{qnum}:broken_clause")

    # Merged multi-prompt theory stems (short, many question verbs)
    verb_hits = len(
        re.findall(
            r"(?i)\b(?:Discuss|Examine|Explain|Elucidate|Comment|Analyse|Analyze|Evaluate|Describe)\b",
            s,
        )
    )
    if verb_hits >= 3 and len(s) < 500:
        if not re.search(r"(?i)\b(?:case|situation|scenario|you are|suppose)\b", s):
            issues.append(f"Q{qnum}:merged_prompts")

    return issues


def _norm_prefix(s: str, n: int = 70) -> str:
    return re.sub(r"\W+", " ", (s or "").lower()).strip()[:n]


def check_paper(gs: str, year: int, questions: list[dict]) -> list[str]:
    issues: list[str] = []
    n = len(questions)
    if n < min_count(gs, year):
        issues.append(f"count={n}<min{min_count(gs, year)}")
    seen_prefix: dict[str, int] = {}
    for i, q in enumerate(questions, start=1):
        stem = str(q.get("question") or "")
        issues.extend(stem_issues(stem, i))
        # Near-duplicate openers within the same paper (e.g. Q5/Q20 same topic cut)
        pref = _norm_prefix(stem, 55)
        if len(pref) >= 40:
            if pref in seen_prefix:
                issues.append(f"Q{i}:near_dup_of_Q{seen_prefix[pref]}")
            else:
                seen_prefix[pref] = i
        exp = expected_marks(gs, year, i, n)
        if exp is not None and i in (1, 11) and year >= 2017 and n >= 20:
            marks = q.get("marks")
            try:
                mf = float(marks) if marks is not None else None
            except (TypeError, ValueError):
                mf = None
            if mf is not None and abs(mf - exp) > 0.01:
                issues.append(f"Q{i}:marks={mf} expected={exp}")
    return issues


def iter_gs_banks(static_root: Path):
    for gs, folder in GS_FOLDERS.items():
        d = static_root / folder
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.json")):
            if not path.stem.isdigit():
                continue
            year = int(path.stem)
            if year < 2013 or year > 2025:
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            yield gs, year, path, data.get("questions") or []


def run_gate(static_root: Path) -> tuple[list[str], int, int]:
    lines: list[str] = []
    ok = fail = 0
    for gs, year, path, questions in iter_gs_banks(static_root):
        issues = check_paper(gs, year, questions)
        if issues:
            fail += 1
            lines.append(
                f"FAIL {gs}/{year} n={len(questions)} {'; '.join(issues[:14])}"
            )
        else:
            ok += 1
            lines.append(f"OK {gs}/{year} n={len(questions)}")
    lines.append("")
    lines.append(f"SUMMARY ok={ok} fail={fail} total={ok + fail}")
    return lines, ok, fail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-root",
        type=Path,
        default=Path("static/upsc"),
        help="Path to static/upsc directory",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write full report text",
    )
    args = parser.parse_args(argv)

    if not args.static_root.exists():
        print(f"static root not found: {args.static_root}", file=sys.stderr)
        return 2

    lines, ok, fail = run_gate(args.static_root)
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
