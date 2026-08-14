#!/usr/bin/env python3
"""Structural booklet OCR predicates and stem splitters for UPSC GS Mains.

These rules target multi-question booklet dumps that survive ordinary garble
filters — e.g. three ``[200 words]`` markers and mid-stem ``10 Many…`` merges.
Shared by the quality gate and Desktop rebuild helpers.
"""

from __future__ import annotations

import re

# Word-limit markers common in older bilingual booklets
WORD_LIMIT = re.compile(
    r"\[\s*\d{2,3}\s*words?\s*\]|\(\s*\d{2,3}\s*words?\s*\)",
    re.I,
)

# Mid-stem marks followed by a capital non-imperative token (merge signature)
# e.g. "[200 words] 10 Many State Governments" / "10 Though Citizens"
MID_MARK_MERGE = re.compile(
    r"(?:"
    r"(?:\[\s*\d{2,3}\s*words?\s*\]|\(\s*\d{2,3}\s*words?\s*\))\s*"
    r"(?:10|12\.5|15|20)\s+"
    r"(?!(?:Discuss|Examine|Explain|Analyse|Analyze|Evaluate|Elucidate|Comment|"
    r"Describe|Highlight|Enumerate|Assess|Critically|What|How|Why|To what|"
    r"Is |Are |Do |Does |Define|Distinguish|Identify|Trace|State |Write |Given )"
    r")"
    r"[A-Z(‘\"“]"
    r"|(?<=\S)\s+(?:10|12\.5|15|20)\s+"
    r"(?!(?:Discuss|Examine|Explain|Analyse|Analyze|Evaluate|Elucidate|Comment|"
    r"Describe|Highlight|Enumerate|Assess|Critically|What|How|Why|To what|"
    r"Is |Are |Do |Does |Define|Distinguish|Identify|Trace|State |Write |Given )"
    r")"
    r"(?:Many|Though|The|In |On |With |resulting|resulting|Although|However|"
    r"Pressure|Recent|Identify|The legitimacy|The Central|Though Citizens)"
    r")",
    re.I,
)

# Orphan / truncated stem ending only with a word-limit box
ENDS_WORD_LIMIT = re.compile(
    r"(?:\[\s*\d{2,3}\s*words?\s*\]|\(\s*\d{2,3}\s*words?\s*\))\s*$",
    re.I,
)

# Starts with OCR junk bang / pipe
BANG_START = re.compile(r"^[!|]\s*")

# Theory stem with multiple independent questions (multiple '?')
# Long multi-part cases are allowed when they contain case markers.
QUESTION_MARKS = re.compile(r"\?")

CASE_HINT = re.compile(
    r"(?i)\b(?:case|situation|scenario|you are|suppose|options available|"
    r"ethical issues|what would you|course of action)\b"
)

# After a terminal '?', a new topic sentence that is NOT a multi-part continuation
# (flags "…modern India? Child cuddling is now…" triple-merges of distinct PYQs)
# Exclusions use word boundaries so "Discuss." / "Does it" both count as continuations.
TOPIC_SHIFT_AFTER_Q = re.compile(
    r"\?\s+(?!"
    r"(?:How|What|Why|Discuss|Examine|Explain|Describe|Analyse|Analyze|"
    r"Evaluate|Elucidate|Comment|Is|Are|Do|Does|To|Which|Whose|Where|When|"
    r"Can|Could|Should|Would|Will|Has|Have|Did|Give|State|Identify|Highlight|"
    r"Trace|Assess|Critically|Also|Further|Additionally|Moreover|Similarly|"
    r"Briefly|Outline|Mention|List|Point|Indicate|Illustrate|Substantiate|"
    r"Justify|Argue|Support|Suggest|Recommend|Compare|Contrast|Distinguish|"
    r"Elaborate|Enumerate|Define|Account|Establish|Bring|Write|Present|"
    r"Keeping|Among|Between|In|On|With|For)\b"
    r")[A-Z][a-z]{2,}"
)

# Incomplete "faced with a [200 words]" style orphans
ORPHAN_FACED_WITH = re.compile(
    r"(?i)\bfaced with a\s*(?:\[\s*\d{2,3}\s*words?\s*\]|\(\s*\d{2,3}\s*words?\s*\))\s*$"
)

# Split points for booklet merges
SPLIT_AT_WORD_LIMIT_MARKS = re.compile(
    r"(?:\[\s*\d{2,3}\s*words?\s*\]|\(\s*\d{2,3}\s*words?\s*\))\s*"
    r"(?:10|12\.5|15|20)\s+",
    re.I,
)
SPLIT_AT_MID_MARK = re.compile(
    r"(?<=[.\"'?])\s+(?:10|12\.5|15|20)\s+(?=[A-Z(‘\"“])",
)


def booklet_stem_issues(stem: str, qnum: int = 0) -> list[str]:
    """Return structural booklet/OCR-merge issues for one stem."""
    s = (stem or "").strip()
    issues: list[str] = []
    prefix = f"Q{qnum}:" if qnum else ""

    if not s:
        issues.append(f"{prefix}empty")
        return issues

    word_limits = WORD_LIMIT.findall(s)
    if len(word_limits) > 1:
        issues.append(f"{prefix}multi_word_limit({len(word_limits)})")

    if MID_MARK_MERGE.search(s):
        issues.append(f"{prefix}mid_mark_merge")

    if BANG_START.match(s):
        issues.append(f"{prefix}bang_start")

    # Truncated orphan: ends with word-limit and body is too short / incomplete
    if ENDS_WORD_LIMIT.search(s):
        body = WORD_LIMIT.sub("", s).strip()
        if len(body) < 60 or ORPHAN_FACED_WITH.search(s) or re.search(
            r"(?i)\bfaced with a\s*$|\bin light of the fact that India is faced with a\s*$",
            body,
        ):
            issues.append(f"{prefix}orphan_word_limit")

    # Multiple independent questions glued (theory only).
    # Many legitimate UPSC stems have 2–4 What/How sub-parts — only flag when
    # co-signaled by booklet merge markers, or a clear topic-shift noun open.
    n_qmarks = len(QUESTION_MARKS.findall(s))
    has_booklet_merge = len(word_limits) > 1 or bool(MID_MARK_MERGE.search(s))
    if (
        n_qmarks >= 3
        and has_booklet_merge
        and not CASE_HINT.search(s)
        and len(s) < 800
    ):
        issues.append(f"{prefix}multi_question_marks({n_qmarks})")
    # Topic shift after '?' (e.g. three distinct GS prompts concatenated)
    if (
        n_qmarks >= 2
        and TOPIC_SHIFT_AFTER_Q.search(s)
        and not CASE_HINT.search(s)
        and len(s) < 900
    ):
        issues.append(f"{prefix}topic_shift_after_q")

    # New full question after an imperative stop: "…. Discuss. Constitutional mechanisms…"
    if (
        re.search(
            r"(?i)\b(?:Discuss|Examine|Elucidate|Comment|Analyse|Analyze)\.\s+"
            r"(?!Critically |Also |Further |Give |State |Identify )"
            r"[A-Z][a-z]{3,}",
            s,
        )
        and not CASE_HINT.search(s)
        and len(s) < 1000
    ):
        issues.append(f"{prefix}topic_shift_after_imperative")

    # Explicit incomplete fragment
    if re.match(r"(?i)^[!|]", s) and len(s) < 200:
        issues.append(f"{prefix}ocr_bang_opener")

    if re.search(r"(?i)^[!|]\s*split\b", s):
        issues.append(f"{prefix}ocr_split_opener")

    return issues


def split_booklet_stem(stem: str) -> list[str]:
    """Best-effort split of a multi-question booklet dump into units.

    Returns one or more cleaned fragments. Callers should re-validate each
    fragment with ``booklet_stem_issues`` / the full gate before writing.
    """
    s = (stem or "").strip()
    if not s:
        return []

    # Prefer split on "[200 words] 10 NextQuestion…"
    parts = SPLIT_AT_WORD_LIMIT_MARKS.split(s)
    if len(parts) == 1:
        parts = SPLIT_AT_MID_MARK.split(s)

    out: list[str] = []
    for part in parts:
        frag = part.strip()
        frag = WORD_LIMIT.sub("", frag).strip()
        frag = re.sub(r"^(?:10|12\.5|15|20)\s+", "", frag).strip()
        frag = re.sub(r"^[!|]\s*", "", frag).strip()
        frag = re.sub(r"\s{2,}", " ", frag).strip()
        if len(frag) >= 28:
            out.append(frag)
    return out if out else ([s] if len(s) >= 28 else [])


def first_clean_unit(stem: str) -> str | None:
    """Return the first booklet-split unit that itself has no booklet issues."""
    for unit in split_booklet_stem(stem):
        if not booklet_stem_issues(unit):
            return unit
    # Try whole stem cleaned of word limits
    cleaned = WORD_LIMIT.sub("", (stem or "")).strip()
    cleaned = re.sub(r"^[!|]\s*", "", cleaned).strip()
    if cleaned and not booklet_stem_issues(cleaned):
        return cleaned
    return None
