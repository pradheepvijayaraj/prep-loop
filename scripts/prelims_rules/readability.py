"""Unreadable stem / option detection (Latin OCR mash, Hindi mix)."""
from __future__ import annotations

import re

_OCR_KNOWN = re.compile(
    r"(?i)\b(Uhaeer|aauecta|fefred|frafafea|fefafar|THR ey|ronly|"
    r"conaider|wqrkshops|tridice|Comwallis|Iikely|shteht)\b"
)


def is_unreadable_text(t: str) -> bool:
    if not t or not str(t).strip():
        return True
    s = str(t).strip()
    if re.search(r"[\u0900-\u097F]", s):
        return True
    if _OCR_KNOWN.search(s):
        return True
    if s.count("\\") >= 2 or s.count("~") >= 3:
        return True

    # letter ratio after stripping digits/currency/punct
    stripped = re.sub(r"[\d,.$₹%°′″()+\-/=]", "", s)
    stripped = re.sub(r"\s+", "", stripped)
    letters = re.findall(r"[A-Za-z]", stripped)
    if len(stripped) >= 28 and letters:
        if len(letters) / max(len(stripped), 1) < 0.55:
            return True

    words = re.findall(r"[A-Za-z']+", s)
    if len(s) >= 40 and len(words) < 3:
        return True
    long_words = [w for w in words if len(w) >= 4]
    if long_words and len(s) >= 40:
        no_vowel = sum(1 for w in long_words if not re.search(r"[aeiouAEIOU]", w))
        # high consonant-only share (OCR mash like Uhaeer still has vowels —
        # also catch high density of weird tokens via known list above)
        if no_vowel / len(long_words) >= 0.45 and no_vowel >= 2:
            return True
    return False


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    s = stem or ""
    words = re.findall(r"[A-Za-z]{2,}", s)

    if re.search(r"[\u0900-\u097F]", s):
        reasons.append("hindi_in_stem")
    if is_unreadable_text(s):
        reasons.append("stem_unreadable")

    if len(words) < 3:
        reasons.append("stem_too_short")

    for i, t in enumerate(opts[:4]):
        if t and is_unreadable_text(t) and len(t) >= 8:
            reasons.append(f"option_unreadable_{i}")

    # dual select-answer lines
    if len(
        re.findall(
            r"(?i)\bselect the (?:answer|correct answer|correct option)",
            s,
        )
    ) >= 2:
        reasons.append("dual_select_interleave")

    return reasons
