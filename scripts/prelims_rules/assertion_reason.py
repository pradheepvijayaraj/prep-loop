"""Assertion–reason (Statement-I / Statement-II) MCQ structural rules."""
from __future__ import annotations

import re

# OCR of Statement-I / Statement-II
_AR_OCR_RE = re.compile(
    r"(?i)("
    r"Statement-!|"          # Statement-!
    r"Statenient|"           # Statenient-11
    r"State\.ment|"
    r"S~atement|"
    r"Statement-11|"         # eleven instead of II
    r"Statement-l\b|"        # lowercase L
    r"Statement-\s*$|"       # truncated "Statement-"
    r"Natio~s|"
    r"thari\b|"
    r"carrieq|"
    r"rat~\s*hikes|"
    r"tare above|"
    r"ihe above|"
    r"is greater continents"
    r")"
)

# Stem looks like A/R pair (must NOT match ordinary "statement is/are correct")
_AR_STEM_RE = re.compile(
    r"(?i)\bStatement[- ]?(?:I{1,3}|IV|!|1|2)\b(?!\s*[a-z]{2,})"
)

# Valid A/R option shape
_AR_OPT_RE = re.compile(
    r"(?i)("
    r"Both Statement|"
    r"Statement-I is correct|"
    r"Statement-II is correct|"
    r"Statement-I is incorrect|"
    r"Statement-II is incorrect|"
    r"correct explanation|"
    r"not the correct explanation|"
    r"does not explain|"
    r"explains Statement"
    r")"
)

# Unrelated topic leakage into A/R options
_OFF_TOPIC_OPT_RE = re.compile(
    r"(?i)("
    r"clonal propagation|horticultural|"
    r"efficacy of drugs|drug trials|"
    r"systemic risk|perfect hedging|"
    r"stock market|fluctuations of a stock|"
    r"beta\b|"
    r"Answer\s*:\s*[A-DX]|Ans\)|"
    r"dropped by UPSC"
    r")"
)


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    s = stem or ""
    joined_opts = "\n".join(opts or [])

    if _AR_OCR_RE.search(s) or _AR_OCR_RE.search(joined_opts):
        reasons.append("ar_ocr_scar")

    # Truncated Statement-I ending mid-phrase with hanging comma (Act,)
    if re.search(
        r"(?i)Wildlife\s*\(Protection\)\s*Act,\s*$",
        s,
        re.M,
    ) or re.search(
        r"(?i)Statement[- ]?I\s*:?\s*[^.\n]{0,80},\s*$",
        s,
        re.M,
    ):
        # only if next non-empty line starts a new Statement / numbered item / Which
        # (hanging mid-sentence before Statement-II is OK when Statement continues)
        if re.search(
            r"(?i)Act,\s*\n\s*(?:Statement|Which|\d+\.)",
            s,
        ) or re.search(r"(?i)Wildlife\s*\(Protection\)\s*Act,\s*$", s, re.M):
            reasons.append("ar_truncated_statement")

    # Numbered prompt as item: "3. Which one of the following is correct"
    if re.search(
        r"(?m)^\s*\d{1,2}\.\s*Which one of the following is correct",
        s,
        re.I,
    ):
        reasons.append("prompt_as_numbered_item")

    is_ar = bool(_AR_STEM_RE.search(s))
    # Classic UPSC A/R ask: "Which one of the following is correct in respect of the above statements?"
    classic_ar_ask = bool(
        re.search(
            r"(?i)which one of the following is correct in respect of the above statements",
            s,
        )
    )
    if is_ar and opts and classic_ar_ask:
        ar_hits = sum(1 for t in opts if _AR_OPT_RE.search(t or ""))
        off = sum(1 for t in opts if _OFF_TOPIC_OPT_RE.search(t or ""))
        if ar_hits < 2:
            reasons.append("ar_options_mismatch")
        if off >= 1:
            reasons.append("ar_options_off_topic")
        # broken labels: "Statement- are correct"
        if re.search(r"(?i)Statement-\s+are correct|Statement-\s+is", joined_opts):
            reasons.append("ar_ocr_scar")

    return reasons
