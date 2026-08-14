"""Code-style options must be covered by numbered stem statements 1..N."""
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
    r"1, 2, 3 and 4 only|1, 2 and 4 only|3 and 4 only"
    r")\b",
    re.I,
)


def numbered_item_numbers(stem: str) -> set[int]:
    """Collect statement numbers from line-start and clear inline lists."""
    nums: set[int] = set()
    s = stem or ""
    # line-start: "1. foo"
    for m in re.finditer(
        r"(?m)^\s*([0-9]{1,2}|I{1,3}|IV|V)[\.)]\s*(\S.+?)\s*$", s
    ):
        raw, body = m.group(1), m.group(2).strip()
        if re.match(
            r"^(Which of the|Select the|How many of the)\b", body, re.I
        ):
            continue
        if raw.isdigit():
            n = int(raw)
        else:
            n = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}.get(raw.upper(), 0)
        if 1 <= n <= 8 and body and not re.match(r"^(19|20)\d{2}$", body[:4] or ""):
            nums.add(n)
    # inline multi-statements: "1. foo 2. bar 3. baz" (same line)
    if len(nums) < 2:
        for m in re.finditer(
            r"(?:^|[\s;])([1-5])[\.)]\s+([A-Za-z(])", s
        ):
            nums.add(int(m.group(1)))
    # Statement-I / Statement-II style
    for m in re.finditer(r"(?i)\bStatement[-\s]?([IVX1-4])\b", s):
        tok = m.group(1).upper()
        roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "1": 1, "2": 2, "3": 3, "4": 4}
        if tok in roman:
            nums.add(roman[tok])
    return nums


def max_option_ref(opts: list[str]) -> int:
    mx = 0
    joined = " ".join(opts or [])
    for m in re.finditer(r"\b([1-5])\b", joined):
        mx = max(mx, int(m.group(1)))
    if re.search(r"\bAll four\b|\b1, 2, 3 and 4\b", joined, re.I):
        mx = max(mx, 4)
    if re.search(r"\bAll three\b|\b1, 2 and 3\b", joined, re.I):
        mx = max(mx, 3)
    return mx


def is_code_options(opts: list[str]) -> bool:
    hits = sum(1 for t in opts if _CODE_OPT_RE.search(t or ""))
    return hits >= 2


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    if not is_code_options(opts):
        return reasons

    need = max_option_ref(opts)
    nums = numbered_item_numbers(stem)
    # real items only (drop orphan high numbers that are select prompts)
    if need >= 2:
        missing = [n for n in range(1, need + 1) if n not in nums]
        if missing:
            # only flag if stem has at least one numbered item (pair/list MCQ)
            # or options clearly code-style with high refs
            if nums or need >= 3:
                reasons.append("code_opts_missing_statements")
        # orphan numbered item with no body / broken tail
        if re.search(r"(?m)^\s*\d+\.\s*$", stem or ""):
            reasons.append("empty_numbered_item")
        # "4. Himalayas being young" where 3 is missing and 4 is fused prompt
        if need >= 4 and 3 not in nums and 4 in nums:
            reasons.append("code_opts_missing_statements")
        if need >= 3 and len(nums) < 2:
            reasons.append("code_opts_insufficient_statements")

    return reasons
