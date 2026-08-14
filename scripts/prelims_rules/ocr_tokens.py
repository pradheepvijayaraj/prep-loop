"""Known OCR scar tokens and mid-phrase list splits."""
from __future__ import annotations

import re

_OCR_TOKEN_RE = re.compile(
    r"\b("
    r"thee|utwo|flow it through|foll\.|Iikely|I2\.|"
    r"Comwallis|tridice|conaider|wqrkshops|Wllich|vis-a-viy|overtord|teason|"
    r"Gément|Fertitizers|fefred|frafafea|fefafar|shteht|NSQFY|"
    r"Uhaeer|aauecta|ronly|THR ey|"
    r"evidences for the\.|said to be the evidences for the\.|"
    r"Statenient|carrieq|thari|Natio~s|tare above|ihe above|"
    r"Statement-!|S~atement|State\.ment|"
    r"cexplanation|"              # not the correct cexplanation
    r"pubic sectore|pubic sector|"  # public sector OCR
    r"tis own|"                   # its own
    r"noé\s+explain|noe\s+explain|"  # does noé explain
    r"vacuu|Col War|neighbow|historic:|"
    r"usc thorium|pow or|Jt can|Chehrisford|"
    r"Kk is|"                     # "It is" OCR as Kk is
    r"remammg|imitative|"         # remaining / initiative
    r"Frontiercs|"                # Frontieres
    r"rewarding the Maternity|"   # regarding
    r"per-delivery and three months per-delivery|"
    r"passes by the|"             # is passed by the
    r"And inter-government"       # An inter-governmental
    r")\b|"
    r"\bI2\.\s|"           # Islands I2. Gulf
    r"\bfoll\.\s*:|"       # foll. :
    r"rat~\s*hikes|"
    r"is greater continents|"
    # grammar OCR glitches — only "is are" (space), NEVER normal "is/are"
    r"\bis are\b|"
    r"\bis are correct\b|"
    r"Statements-II is are|"
    r"correct A\)\s*$|"
    r"\bin th East\b|"     # "in the East" OCR — not "North Eastern"
    r"given abo is/are|"
    r"_ experiment|"
    r"_ Combat|"
    r"satellite navigation fol|"
    r"Montague-Chehrisford|"
    r"Selected the Corrected|"
    r"Select(?:ed)? the Corrected answer|"
    r"Neither 1 Or 2|"
    r"Statements\s*-\s*I\s*:|"   # Statements - I: (plural)
    r"Statements\s*-\s*II\s*:|"
    r"objectives of Constitution has been as one of the Indian provided",
    re.I,
)

# Mid-phrase numbered-item ends — only short incomplete bodies (≤6 words)
# e.g. "1. small and." / "2. Ash and" — not long fused select tails.
_MID_SPLIT_RE = re.compile(
    r"(?m)^\s*\d{1,2}\.\s*((?:\S+\s+){0,5}\S+)\s*$",
    re.I,
)
_MID_END_WORDS = re.compile(
    r"\b(and|of|the|for|to|in|on|with|from|as|by|or)\s*\.?\s*$", re.I
)
# Glue scar inside item: "...project. small and.\n2. Enterprises"
_MID_SPLIT_INLINE_RE = re.compile(
    r"\b(small and|large and|medium and)\s*\.?\s*$",
    re.I | re.M,
)


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    s = stem or ""
    joined = s + "\n" + "\n".join(opts or [])

    if _OCR_TOKEN_RE.search(joined):
        reasons.append("ocr_scar_token")

    # "Islands I2. Gulf" style digit-letter OCR
    if re.search(r"[A-Za-z]\s*I\d+\.\s*[A-Za-z]", s):
        reasons.append("ocr_scar_token")

    # mid-phrase list splits (2026 Q97 class)
    if _MID_SPLIT_INLINE_RE.search(s):
        reasons.append("mid_phrase_list_split")
    else:
        for m in _MID_SPLIT_RE.finditer(s):
            body = m.group(1) or ""
            if _MID_END_WORDS.search(body) and len(body.split()) <= 6:
                reasons.append("mid_phrase_list_split")
                break

    # pair-table word split: "Arunachal The capital ... Pradesh"
    if re.search(
        r"(?i)\b(Arunachal|Madhya|Uttar|Andhra|Himachal|West)\b.+\b("
        r"Pradesh|Bengal)\b",
        s,
    ) and re.search(r"(?i)(capital|state|description|came into)", s):
        # description jammed between multi-token state name
        if re.search(
            r"(?i)Arunachal\s+The\s+capital|Madhya\s+The\s+|Uttar\s+The\s+",
            s,
        ):
            reasons.append("pair_table_word_split")

    return reasons
