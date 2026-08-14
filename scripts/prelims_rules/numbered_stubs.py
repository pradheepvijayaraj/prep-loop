"""Numbered list item stub detection (Detection of / If the / fused prompts)."""
from __future__ import annotations

import re

_MID_PHRASE_END_RE = re.compile(
    r"\b(of|for|and|the|to|in|on|with|from|as|by|or)\s*$", re.I
)
_STUB_BODY_RE = re.compile(
    r"^(?:"
    r"If the|Which of the|How many of the above.*|How many|How$|"
    r"Detection of\.?|Detection of the|Detection of|"
    r"Ash and|Pyroclastic$|"
    r"Cashew Papaya Red|"
    r"Rafael MiG-?$|MiG-?$|Tejas MK-?$|"
    r"Lipstick Lead Soft|Lead Soft$|"
    r"It\.?$|Terms\.?$|Context\.?$|Topic\.?$|"
    r"Commonly$|Unwanted$|Brominated$|Chinese$|Monosodium$|"
    r"Spreading$|Increasing the$|Capturing$|"
    r"River$|Flows in$|Site$|Well$"
    r")$",
    re.I,
)
_PURE_DEBRIS = {
    "how", "which", "if", "the", "and", "of", "for", "to", "in", "on",
    "detection", "commonly", "unwanted", "terms", "context", "topic",
}


def numbered_lines(stem: str) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    for m in re.finditer(
        r"(?m)^\s*([0-9]{1,2}|I{1,3}|IV|V)[\.)]\s*(.+?)\s*$", stem or ""
    ):
        raw, body = m.group(1), m.group(2).strip()
        if raw.isdigit():
            n = int(raw)
        else:
            n = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}.get(raw.upper(), 0)
        if n and body:
            items.append((n, body))
    return items


def is_stub_body(body: str) -> bool:
    core = body.rstrip(" .;:")
    if not core:
        return True
    if _STUB_BODY_RE.match(core):
        return True
    m_fused = re.search(
        r"\b(How many of the above|Which of the above|Which of the statements|"
        r"Select the answer|Select the correct)\b",
        body,
        re.I,
    )
    if m_fused:
        pre = body[: m_fused.start()].strip(" .;:")
        if not pre or len(pre.split()) <= 2:
            return True
        return False
    if _MID_PHRASE_END_RE.search(core) and len(core.split()) <= 4:
        return True
    toks = core.split()
    if len(toks) == 1:
        low = core.lower().rstrip(".")
        if low in _PURE_DEBRIS or low in {
            "they", "it", "this", "that", "what", "how", "i", "ii", "iii",
        }:
            return True
        if re.match(r"^[ivxIVX]{1,4}\.?$", core):
            return True
        if len(core) <= 1:
            return True
        if re.match(r"^\d+$", core):
            return True
        return False
    return False


def check(stem: str, opts: list[str]) -> list[str]:
    reasons: list[str] = []
    items = numbered_lines(stem)
    stubs = [(n, b) for n, b in items if is_stub_body(b)]

    def severe(b: str) -> bool:
        core = b.rstrip(" .;:")
        if re.match(r"^[ivxIVX]{1,4}\.?$", core):
            return True
        if re.match(
            r"^(If the|Detection of|Detection of the|Which of the|How many|How)$",
            core,
            re.I,
        ):
            return True
        if _MID_PHRASE_END_RE.search(core) and len(core.split()) <= 4:
            return True
        if len(core) <= 2:
            return True
        if re.match(r"^(19|20)\d{2}$", core) or re.match(r"^\d+$", core):
            return True
        return False

    if any(severe(b) for _, b in stubs):
        reasons.append("stub_numbered_lines")
        reasons.append("stub_only_item")
    elif len(stubs) >= 2:
        reasons.append("stub_numbered_lines")

    if items and len(stubs) == len(items) and len(items) >= 2:
        reasons.append("all_items_stubs")

    # select prompt as numbered item (any variant of the UPSC select/which tail)
    if any(
        re.match(
            r"^(Which of (?:the )?(?:following |statement|statements)|"
            r"Select(?:ed)? the (?:answer|correct|Corrected)|"
            r"How many of the (?:above|statements))\b",
            b,
            re.I,
        )
        for _, b in items
    ):
        reasons.append("prompt_as_numbered_item")
    # Numbered select/which tails — only list indices 1–15, never years (2016./2030.)
    for m in re.finditer(
        r"(?m)^\s*(\d{1,2})\.\s*Which of (?:the )?(?:following |statement)",
        stem or "",
        re.I,
    ):
        if 1 <= int(m.group(1)) <= 15:
            reasons.append("prompt_as_numbered_item")
            break
    for m in re.finditer(
        r"(?m)^\s*(\d{1,2})\.\s*Select(?:ed)? the (?:answer|Corrected)",
        stem or "",
        re.I,
    ):
        if 1 <= int(m.group(1)) <= 15:
            reasons.append("prompt_as_numbered_item")
            break

    # mangled A/R as numbered "1. Statements - I:" / "2. Statements - II:"
    if re.search(
        r"(?m)^\s*\d+\.\s*Statements?\s*[-–]?\s*I{1,2}\s*:",
        stem or "",
        re.I,
    ):
        reasons.append("ar_numbered_statements_label")

    # roman label as item 1: "1. i."
    if re.search(r"(?m)^\s*1\.\s*[iI]\.?\s*$", stem or ""):
        reasons.append("roman_label_as_item")

    # false qnum break: classes 9 and\n12. Which
    if re.search(
        r"(?is)(?:classes|standards|grades?|class)\s+\d+\s+and\s*\n\s*\d{1,2}\.\s*"
        r"(?:Which|Select|How many)",
        stem or "",
    ):
        reasons.append("false_qnum_list_break")

    return reasons
