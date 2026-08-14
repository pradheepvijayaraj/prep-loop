"""Option-text sanity: chrome, truncated None-of, OCR glue, nonsense shorts."""
from __future__ import annotations

import re

_CODE_OPT_RE = re.compile(
    r"\b("
    r"1 only|2 only|3 only|4 only|5 only|"
    r"1 and 2(?: only)?|1 and 3(?: only)?|1 and 4(?: only)?|"
    r"2 and 3(?: only)?|2 and 4(?: only)?|3 and 4(?: only)?|"
    r"1, 2 and 3|1, 2, 3 and 4|1, 2, 3, 4 and 5|"
    r"2, 3 and 4|3, 4 and 5|1, 3 and 4|1, 2 and 4|"
    r"Both 1 and 2|Neither 1 nor 2|"
    r"Only one|Only two|Only three|All (?:three|four|the three)|None|"
    r"I only|II only|Both I and II|Neither I nor II"
    r")\b",
    re.I,
)

# Answer-key / exam-chrome pollution inside option text
_CHROME_RE = re.compile(
    r"(?i)("
    r"Answer\s*:\s*[A-DX]|"
    r"Ans\s*\)|"
    r"Ans\s*:|"
    r"Question has been dropped by UPSC|"
    r"dropped by UPSC|"
    r"Share this:|ForumIAS|WhatsApp|Click to share|"
    r"B-APM-P-CKB|CYRF-F-TXLI"
    r")"
)

_TRUNC_NONE_RE = re.compile(
    r"(?i)^None of the(?: statements)?\s*\([aA]\)\s*,?\s*$"
)
_TRUNC_BOTH_RE = re.compile(r"(?i)^Both\s*\([A-Da-d]\)\s*and\s*$")

# OCR-glued code options: "1, 2 and.3", "Neither 1 not 2", "1, 2 and 3 ronly"
_OCR_CODE_GLITCH_RE = re.compile(
    r"(?i)("
    r"\band\.\s*\d|"        # and.3 (not "land. 3")
    r"\bnot 2\b|"           # Neither 1 not 2
    r"\bronly\b|"
    r"\b1 onlyy\b|"
    r"\b61,\s*2\b|"
    r"and\.\s*4\b|"
    r"\*\s*aa\b|"
    r"FIG\s*1,|"
    r"4H\s*5|"
    r"cexplanation|"
    r"\bis are\b|"
    r"Statements-II is are|"
    r"does no[eé]\s+explain|"
    r"correct A\)\s*$|"
    r"\bpubic sectore\b|"
    r"Neither 1 Or 2|"
    r"\b1and 2\b"  # missing space "1and 2"
    r")"
)

_MATCH_MATRIX_RE = re.compile(
    r"(?i)Code\s*:\s*A\s*B\s*C\s*D|^\s*[aA]\)\s*\d\s+\d\s+\d\s+\d"
)


def is_code_style(t: str) -> bool:
    return bool(_CODE_OPT_RE.search(t or ""))


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    if len(opts) < 4:
        reasons.append("fewer_than_4_options")

    for i, t in enumerate(opts[:4]):
        if not t:
            reasons.append(f"blank_option_{i}")
            continue
        if len(t) > 280:
            reasons.append(f"option_overlong_{i}")
        if _CHROME_RE.search(t):
            reasons.append(f"option_answer_chrome_{i}")
        if _TRUNC_NONE_RE.match(t.strip()) or _TRUNC_BOTH_RE.match(t.strip()):
            reasons.append(f"option_truncated_{i}")
        if re.search(r"(?i)\b(and|the|of|to|for|a|an|or)\s*$", t.strip()) and len(
            t.split()
        ) <= 4:
            reasons.append(f"option_truncated_{i}")
        if _OCR_CODE_GLITCH_RE.search(t):
            reasons.append(f"option_ocr_glitch_{i}")
        if _MATCH_MATRIX_RE.search(t):
            reasons.append(f"option_match_matrix_{i}")
        # Ultra-short non-code nonsense: "WT", "aa", "haat" (not "None", "1 only")
        core = t.strip()
        if len(core) <= 3 and not is_code_style(core) and not re.match(
            r"^\d+$", core
        ):
            # allow country codes / short real answers only if all-alpha common words
            if re.match(r"^[A-Za-z]{1,3}$", core) and core.upper() not in {
                "USA", "UAE", "UK", "EU", "UN", "GDP", "IMF", "RBI", "WTO", "WHO",
                "UNO", "BJP", "INC", "CPI", "NDA", "UPA", "GST", "FDI", "SDR",
            }:
                # WT is not WTO — flag single-token 1–3 letter non-acronyms that
                # aren't known orgs; WT specifically, and any 1–2 letter junk
                if core.upper() in {"WT", "AA", "BB", "XX", "YY", "ZZ"} or len(core) <= 2:
                    reasons.append(f"option_nonsense_short_{i}")
        # known truncated org
        if re.match(r"(?i)^WT$", core):
            reasons.append(f"option_nonsense_short_{i}")
        if re.search(r"^\s*\((?:e|bj|fc|dq|bJ)\)\s*", t) or re.search(
            r"\b1 and 8\d\s+only\b", t, re.I
        ):
            reasons.append(f"option_ocr_label_{i}")

    return reasons
