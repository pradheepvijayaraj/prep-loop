#!/usr/bin/env python3
"""Prelims GS1 OCR-scar scan and pure-text repair helpers.

Used by convert hardening tests and year-by-year cleanup.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# High-severity scar detection
# ---------------------------------------------------------------------------

_CODE_OPT_RE = re.compile(
    r"\b(1 and 2|2 and 3|3 and 4|1 and 3|1 only|2 only|3 only|4 only|"
    r"1, 2 and 3|1, 2, 3 and 4|2, 3 and 4|3, 4 and 5|1, 2, 3, 4 and 5)\b",
    re.I,
)

_HINDI_RE = re.compile(r"[\u0900-\u097F]")
_OCR_TOKEN_RE = re.compile(
    r"\b(Jects|enwepreneurs|Ciovern|bfGh|Harapphey|stk fewer|wet wet|"
    r"Beal\b|iianoparticles|whit\s|ans,\.ver|beJ\s*ow|"
    r"Comwallis|tridice|conaider|wqrkshops|Wllich|vis-a-viy|overtord|teason|"
    r"Gément|Fertitizers|fefred|frafafea|fefafar|utwo|thee|"
    r"flow it through|shteht|NSQFY|foll\.|Iikely|Uhaeer|aauecta|ronly|"
    r"THR ey|cexplanation|pubic sectore|tis own|noé\s+explain|"
    r"vacuu|Col War|neighbow|usc thorium|pow or|Kk is|Chehrisford|"
    r"remammg|imitative|Frontiercs|rewarding the Maternity|passes by the)\b|"
    r"\bI2\.\s|Answer\s*:\s*[A-DX]|Ans\)|dropped by UPSC|\band\.\s*\d|"
    r"Neither 1 not 2|Neither 1 Or 2|\bis are\b|Statements-II is are|correct A\)\s*$|"
    r"\bin th East\b|_ experiment|_ Combat|"
    r"satellite navigation fol|Montague-Chehrisford|"
    r"Selected the Corrected|Select(?:ed)? the Corrected answer|"
    r"Statements\s*-\s*I\s*:|Statements\s*-\s*II\s*:|"
    r"objectives of Constitution has been as one of the Indian provided",
    re.I,
)
_OCR_SYMBOL_RE = re.compile(
    r"[@¥]|fir\s*=\s*F|stg\s+afifcen|writs\s+stg|\\\\|~{2,}|\\f\\~",
    re.I,
)


def option_texts(options: list | None) -> str:
    parts: list[str] = []
    for o in options or []:
        if isinstance(o, dict):
            parts.append(str(o.get("text") or ""))
        else:
            parts.append(str(o))
    return " ".join(parts)


def count_numbered_statements(stem: str) -> int:
    """Count distinct numbered list items (line-start or clear inline)."""
    s = stem or ""
    # Allow optional space after marker: "1.Cow" or "1. Cow" or bare "1 Global"
    line = len(re.findall(r"(?m)^\s*(?:\d+|I{1,3}|IV|V|Q\d+)[\.)]?\s+\S", s))
    if line >= 2:
        return line
    paren = len(re.findall(r"\(\s*\d+\s*\)\s*\.?\s*\S", s))
    if paren >= 2:
        return paren
    inline = len(re.findall(r"(?:^|\s)(?:\d+|I{1,3}|IV|V)\s*[\.)]?\s*\S", s))
    if inline >= 2:
        return inline
    # bare "1 Word 2 Word" (no punctuation after number)
    bare = len(re.findall(r"(?:^|\s)\d{1,2}\s+[A-Z(]", s))
    return bare


def high_severity_scars(stem: str, options: list | None = None) -> list[str]:
    s = stem or ""
    out: list[str] = []
    opts = option_texts(options)

    # glued colon pairs without numbered structure
    if re.search(r"[A-Za-z]{3,}\s*:\s*[A-Za-z]{3,}\s+[A-Za-z]{3,}\s*:", s):
        if count_numbered_statements(s) < 2 and s.count("\n") < 3:
            out.append("glued_colon_pairs")

    if re.search(r"(?m)^\d+[\.)]\s+.+\sSelect the (?:answer|correct)", s, re.I):
        out.append("select_glued_in_item")

    # Same-line glue only (do not treat "\n\nSelect the answer" as a scar)
    # Do not flag the normal instruction phrase "and select the answer".
    # A real glue scar has the answer instruction appended after question text.
    if re.search(r"[^\n][ \t]+(?<!and )Select the answer", s, re.I):
        out.append("select_glued_inline")
    if re.search(r"(?i)Selected the Corrected|Select(?:ed)? the Corrected answer", s):
        out.append("select_ocr_chrome")
    for m in re.finditer(
        r"(?m)^\s*(\d{1,2})\.\s*Which of (?:the )?(?:following |statement)",
        s,
        re.I,
    ):
        if 1 <= int(m.group(1)) <= 15:
            out.append("prompt_as_numbered_item")
            break
    if re.search(r"(?m)^\s*\d+\.\s*Statements?\s*[-–]?\s*I{1,2}\s*:", s, re.I):
        out.append("ar_numbered_statements_label")
    if _HINDI_RE.search(s):
        out.append("hindi_mash")

    if re.search(r"(?m)^\s*\d+[\.)]\s*Select the", s, re.I):
        out.append("numbered_select")

    if re.search(r"(?m)^\s*\d+[\.)]\s*$", s):
        out.append("empty_numbered")

    if _OCR_TOKEN_RE.search(s):
        out.append("ocr_typo_token")

    if _OCR_SYMBOL_RE.search(s):
        out.append("ocr_symbol_garbage")

    if _CODE_OPT_RE.search(opts):
        if count_numbered_statements(s) < 2:
            out.append("code_opts_no_statements")

    for o in options or []:
        t = (o.get("text") if isinstance(o, dict) else str(o)) or ""
        if not str(t).strip():
            out.append("blank_option")
            break
        if re.search(r"^None of the\s*\([aA]\)\s*,?\s*$", str(t).strip(), re.I):
            out.append("truncated_none_of_option")
            break
        if re.search(r"Code\s*:\s*A\s*B\s*C\s*D", str(t), re.I):
            out.append("match_matrix_in_option")
            break
        # nonsense / OCR-mash option
        letters = re.findall(r"[A-Za-z]", str(t))
        non_space = re.sub(r"\s+", "", str(t))
        if len(non_space) >= 16 and letters and len(letters) / max(len(non_space), 1) < 0.50:
            out.append("unreadable_option")
            break
        if str(t).count("\\") >= 2 or str(t).count("~") >= 3:
            out.append("unreadable_option")
            break

    # unreadable stem (Latin OCR mash / low letter ratio) — ignore digits/currency
    stripped = re.sub(r"[\d,.$₹%°()+\-/=]", "", s)
    stripped = re.sub(r"\s+", "", stripped)
    letters = re.findall(r"[A-Za-z]", stripped)
    if len(stripped) >= 28 and letters and len(letters) / max(len(stripped), 1) < 0.55:
        out.append("unreadable_stem")
    words = re.findall(r"[A-Za-z']+", s)
    long_words = [w for w in words if len(w) >= 4]
    if long_words and len(s) >= 40:
        no_vowel = sum(1 for w in long_words if not re.search(r"[aeiouAEIOU]", w))
        if no_vowel / len(long_words) >= 0.45 and no_vowel >= 2:
            out.append("unreadable_stem")

    if re.search(r"\b(3,\s*4 and 5|3,4 and 5|1, 2, 3, 4 and 5)\b", opts, re.I):
        n_stmt = len(re.findall(r"(?m)^\s*[1-9][\.)]\s+\S", s))
        if n_stmt < 5:
            out.append("option_refs_missing_statements")

    # pipe OCR artifacts
    if re.search(r"\|\s*\|", s) or re.search(r"\s\|\s", s):
        if s.count("|") >= 2:
            out.append("pipe_ocr_noise")

    # Web chrome / scrape pollution in stem or options
    chrome_re = re.compile(
        r"(Share this:|Click to share|WhatsApp|ForumIAS|©\s*ForumIAS|"
        r"Post navigation|Privacy Policy|Stay Ahead in Your UPSC|"
        r"Get Access & Download|upsc\.gov|B-APM-P-CKB|NAINTEIN)",
        re.I,
    )
    if chrome_re.search(s) or chrome_re.search(opts):
        out.append("web_chrome_pollution")

    # Option OCR labels like (bj) (fc} (dq) (5) embedded wrong
    if re.search(r"\((?:bj|fc|dq|fd|bo|ce)\b|fc\}|\(bJ\)|\(5\)|\{d\)", opts, re.I):
        out.append("option_ocr_labels")

    # Two-column / dual-question interleave
    if re.search(r"(?m)^\s*\d+\.\s+.+\n\s*\d+\.\s+", s) and s.lower().count("select the") >= 2:
        out.append("dual_select_interleave")
    if re.search(r"\b\d{2}\.\s+The[- ]", s):  # embedded "75. The-Reserve"
        out.append("embedded_qnum_interleave")
    # interleaved two topics: bankers bank + money supply fused
    if re.search(r"bankers.? bank", s, re.I) and re.search(r"money supply", s, re.I):
        if len(s) > 400:
            out.append("two_topic_interleave")

    # Word-split multiword proper names as separate numbered items
    # e.g. "1. Donyi\n2. Polo\n3. Airport" when options are 1 and 2 only (3 items expected)
    numbered_items = re.findall(r"(?m)^\s*(\d+)[\.)]\s*(.+)$", s)
    if numbered_items and _CODE_OPT_RE.search(opts):
        single_word = sum(1 for _, body in numbered_items if len(body.strip().split()) == 1)
        if len(numbered_items) >= 4 and single_word >= 3:
            # and bodies include generic words like Airport/International
            bodies = " ".join(b for _, b in numbered_items).lower()
            if re.search(r"\b(airport|international|polo|programme|children.?s|commissioner)\b", bodies):
                out.append("word_split_list")

    # Heavy option garbage length (chrome pasted into option)
    for o in options or []:
        t = (o.get("text") if isinstance(o, dict) else str(o)) or ""
        if len(t) > 400:
            out.append("option_overlong_chrome")
            break
        if re.search(r"[\u0900-\u097F]", t) and not re.search(r"[\u0900-\u097F]", s):
            # Hindi only in options while stem English = often OCR mash
            if len(t) > 40:
                out.append("option_hindi_garbage")
                break

    # Common OCR stem typos that mark unreadability
    if re.search(r"\b(inerease|monetaty|carrect|puble|fands|Biteoins|countnes|implctncnta|scen in the news|ore Banking)\b", s, re.I):
        out.append("severe_ocr_typo")


    # Exam booklet codes in options (CYRF-F-TXLI, 1 and 83 only)
    if re.search(r"\b\d+\s+and\s+8\d\s+only\b", opts, re.I) or re.search(
        r"\b[A-Z]{3,}-[A-Z]-[A-Z]{2,}\b|\bCYRF\b|\bTXLI\b", opts
    ):
        out.append("exam_booklet_code_option")
    if re.search(r"\(e\)\s*\d+\s+only", opts, re.I):
        out.append("option_ocr_letter_e")

    # Leading paper Q number leftover: "79. Consider"
    if re.match(r"^\s*\d{1,3}\.\s+(Consider|Which|With reference|How|What)", s):
        out.append("leading_paper_qnum")

    # False mid-number list breaks: line is ONLY "25. Members" / "18. States" etc.
    if re.search(
        r"(?m)^\s*\d+\.\s+(Members|States|PVTGs|Hours|Members of the Lok Sabha)\s*$",
        s,
        re.I,
    ):
        out.append("false_number_list_break")
    if re.search(r"not more than\s*\n\s*\d+\.\s+", s, re.I):
        out.append("false_number_list_break")
    # "reside in\n18. States" style split across lines
    if re.search(r"(?m)(in|are|than|of)\s*\n\s*\d+\.\s+(States|Members|PVTGs|Hours)\b", s, re.I):
        out.append("false_number_list_break")

    # Fragment lines: incomplete phrases like "Commission for." "Stability and." "of the."
    frag_lines = re.findall(r"(?m)^\s*\d+[\.)]\s*(.+)$", s)
    short_frags = sum(
        1
        for b in frag_lines
        if re.search(
            r"\b(and|of the|for|the|Pact of the|Stability and|Commission for|Exchange-Traded|Association of|South-East|Asia-Pacific)\s*\.?$",
            b.strip(),
            re.I,
        )
        or re.match(r"^(Statement-I|Statement-II|Statement)\s+The\s*$", b.strip(), re.I)
    )
    if short_frags >= 2 and len(frag_lines) >= 3:
        out.append("fragment_numbered_lines")

    # Pair table exploded: "1. Terms 2. Context 3. Topic"
    if re.search(r"(?m)^\s*1\.\s*Terms\s*$", s, re.I) or re.search(
        r"1\.\s*Terms\s*\n\s*2\.\s*Context", s, re.I
    ):
        out.append("pair_table_header_as_items")

    # Vitamin/disease word-split style
    if re.search(r"Vitamin Deficiency\s*\n\s*\d+\.\s*Vitamin", s, re.I):
        out.append("pair_word_split")
    if re.search(r"(?m)^\s*\d+\.\s*C Scurvy", s) or re.search(r"(?m)^\s*\d+\.\s*D Rickets", s):
        out.append("pair_word_split")

    # Double numbering "1. 1. Right"
    if re.search(r"(?m)^\s*1\.\s*1\.\s+", s) or re.search(r"\b1\.\s*1\.\s+", s):
        out.append("double_numbering")

    # Severe content OCR tokens
    if re.search(
        r"\b(Crycurrency|Artificial experiment|Trular|gram Sabah|i found|have such a form of movements\. Correct)\b",
        s,
        re.I,
    ):
        out.append("severe_content_ocr")


    return out


# ---------------------------------------------------------------------------
# Pure repairs
# ---------------------------------------------------------------------------

_SELECT_RE = re.compile(
    r"\s*(Select the (?:answer|correct)[^\n]*)$", re.I | re.S
)


def already_numbered_list(body: str) -> bool:
    return count_numbered_statements(body) >= 2


def fix_select_glued(stem: str) -> str:
    s = stem or ""
    # Ensure blank line before any "Select the …" prompt
    s = re.sub(
        r"(?<!\n)\n?(Select the (?:answer|correct)[^\n]*)$",
        r"\n\n\1",
        s,
        flags=re.I | re.M,
    )
    s = re.sub(
        r"(?m)([^\n])[ \t]+(Select the (?:answer|correct)[^\n]*)$",
        r"\1\n\n\2",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"(\d+[\.)]\s+[^\n]+?)[ \t]+(Select the (?:answer|correct)[^\n]*)",
        r"\1\n\n\2",
        s,
        flags=re.I,
    )
    # strip bogus "N. Select the..."
    s = re.sub(r"(?m)^\s*\d+[\.)]\s*(Select the)", r"\1", s, flags=re.I)
    # Also catch "Select the answer from the following" glued after period on prior line
    s = re.sub(
        r"(?m)([.!?])\n(Select the )",
        r"\1\n\n\2",
        s,
        flags=re.I,
    )
    return re.sub(r"\n{3,}", "\n\n", s).strip()

def fix_pipe_noise(stem: str) -> str:
    s = re.sub(r"\s*\|\s*\|\s*", " ", stem or "")
    s = re.sub(r"\s\|\s", " ", s)
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def fix_glued_colon_pairs(stem: str) -> str | None:
    """Repair 'Name : Place Name : Place' match lists into numbered pairs."""
    if not re.search(r"correctly matched|following pairs|match", stem or "", re.I):
        return None
    if (stem or "").count(":") < 2:
        return None
    s = stem
    select_m = _SELECT_RE.search(s)
    select_tail = select_m.group(1).strip() if select_m else ""
    body = s[: select_m.start()] if select_m else s
    body_n = re.sub(r":\s*\n+\s*\d+\.\s*", ": ", body)
    body_n = re.sub(r"\s+", " ", body_n).strip()
    intro_m = re.search(
        r"(.+?(?:not\s+)?correctly matched\s*\??|.+?following pairs\s*:?\s*)",
        body_n,
        re.I,
    )
    if not intro_m:
        return None
    intro = intro_m.group(1).strip()
    rest = body_n[intro_m.end() :].strip()
    pairs = re.findall(r"([A-Za-z][A-Za-z'\-]+)\s*:\s*([A-Za-z][A-Za-z'\-]+)", rest)
    if len(pairs) < 2:
        return None
    lines = [f"{i + 1}. {a} : {b}" for i, (a, b) in enumerate(pairs)]
    out = intro.rstrip(":") + "\n\n" + "\n".join(lines)
    if select_tail:
        out += "\n\n" + select_tail
    elif re.search(r"select the answer", stem, re.I):
        out += "\n\nSelect the answer using the code given below:"
    return out


def fix_inline_numbered_to_multiline(stem: str) -> str | None:
    """Turn '…? 1. foo 2. bar 3. baz Select…' into multiline numbered list."""
    s = stem or ""
    if already_numbered_list(s) and re.search(r"(?m)^\s*\d+[\.)]\s+", s):
        # already multiline-ish
        if s.count("\n") >= 2:
            return None
    select_m = _SELECT_RE.search(s)
    select_tail = ""
    core = s
    if select_m:
        select_tail = "\n\n" + select_m.group(1).strip()
        core = s[: select_m.start()]
    core_one = re.sub(r"\s+", " ", core).strip()
    # Normalize Q1) / (1). / 1)
    core_one = re.sub(r"\bQ(\d+)\)\s*", r"\1. ", core_one)
    core_one = re.sub(r"\(\s*(\d+)\s*\)\s*\.?\s*", r"\1. ", core_one)
    core_one = re.sub(r"(?<!\d)(\d+)\)\s+", r"\1. ", core_one)
    if not re.search(r"(?:^|\s)1\.\s+\S.+\s2\.\s+", core_one):
        return None
    parts = re.split(r"(?:(?<=\s)|^)([1-9]\d*)\.\s+", core_one)
    if len(parts) < 5:
        return None
    intro = parts[0].strip()
    items: list[str] = []
    for j in range(1, len(parts), 2):
        num = parts[j]
        text = parts[j + 1].strip() if j + 1 < len(parts) else ""
        text = re.sub(r"\s+", " ", text).strip(" .;")
        if text:
            items.append(f"{num}. {text}")
    if len(items) < 2:
        return None
    return intro + "\n\n" + "\n".join(items) + select_tail


def fix_unnumbered_items_for_code_options(stem: str, options: list | None) -> str | None:
    """When options are code-style but stem has no numbers, number capitalised items."""
    opts = option_texts(options)
    if not _CODE_OPT_RE.search(opts):
        return None
    if count_numbered_statements(stem or "") >= 2:
        return None
    one = re.sub(r"\s+", " ", stem or "").strip()
    select_m = _SELECT_RE.search(one)
    select_tail = ""
    if select_m:
        select_tail = "\n\n" + select_m.group(1).strip()
        one = one[: select_m.start()].strip()
    m = re.match(r"^(.+\?)\s+(.+)$", one)
    if not m:
        return None
    intro, rest = m.group(1).strip(), m.group(2).strip()
    if len(rest) < 8:
        return None
    # comma-separated
    if rest.count(",") >= 1 and rest.count(",") <= 6:
        items = [x.strip(" .;") for x in rest.split(",") if x.strip()]
        if 2 <= len(items) <= 8:
            numbered = [f"{i + 1}. {it}" for i, it in enumerate(items)]
            return intro + "\n\n" + "\n".join(numbered) + select_tail
    # single-word country/org list
    words = rest.split()
    if 2 <= len(words) <= 6 and all(re.match(r"^[A-Z][A-Za-z\-]+$", w) for w in words):
        numbered = [f"{i + 1}. {w}" for i, w in enumerate(words)]
        return intro + "\n\n" + "\n".join(numbered) + select_tail
    # multi-word items separated by known end tokens
    items = re.split(
        r"(?<=Convention)\s+(?=[A-Z])|(?<=Project)\s+(?=[A-Z])|(?<=Highway)\s+(?=[A-Z])|"
        r"(?<=Federation)\s+(?=[A-Z])|(?<=Party of India)\s+(?=[A-Z])|"
        r"(?<=Establishments)\s+(?=[A-Z])|(?<=undertakings)\s+(?=[A-Z])|"
        r"(?<=restaurants)\s+(?=[A-Z])|(?<=gram)\s+(?=[A-Z])|"
        r"(?<=millet)\s+(?=[A-Z])|(?<=pea)\s+(?=[A-Z])",
        rest,
        flags=re.I,
    )
    items = [re.sub(r"\s+", " ", x).strip(" .;") for x in items if x and len(x.strip()) > 2]
    if 2 <= len(items) <= 8:
        numbered = [f"{i + 1}. {it}" for i, it in enumerate(items)]
        return intro + "\n\n" + "\n".join(numbered) + select_tail
    return None


_OCR_FIXES = [
    (re.compile(r"\bCiovern\s*\.?\s*ment", re.I), "Government"),
    (re.compile(r"\bCiovern\b", re.I), "Govern"),
    (re.compile(r"\bJects\b", re.I), "Jets"),
    (re.compile(r"\benwepreneurs\b", re.I), "entrepreneurs"),
    (re.compile(r"\biianoparticles\b", re.I), "nanoparticles"),
    (re.compile(r"\bans,\.ver\b", re.I), "answer"),
    (re.compile(r"\bbeJ\s*ow\b", re.I), "below"),
    (re.compile(r"\bwhit\s+", re.I), "with "),
    (re.compile(r"\bSu-30 MKT Fighter Jets\b", re.I), "Su-30 MKI Fighter Jets"),
]


def apply_ocr_token_fixes(stem: str) -> str:
    s = stem or ""
    for pat, rep in _OCR_FIXES:
        s = pat.sub(rep, s)
    return s




def number_statement_sentences(stem: str, options: list | None = None) -> str | None:
    """Number plain-sentence statements when options are code-style."""
    opts = option_texts(options)
    if not _CODE_OPT_RE.search(opts):
        return None
    s = stem or ""
    if count_numbered_statements(s) >= 2:
        return None
    select_m = _SELECT_RE.search(s)
    select_tail = ""
    core = s
    if select_m:
        select_tail = "\n\n" + select_m.group(1).strip()
        core = s[: select_m.start()]
    core = re.sub(r"\s+", " ", core).strip()
    # Pattern: intro ending with statements/following/? then body of 2+ sentences
    # Prefer intro ending at '?' (standard UPSC) then body sentences.
    m = re.match(r"^(?P<intro>.+\?)\s+(?P<body>.+)$", core)
    if not m:
        # "Consider the following statements: Body..."
        m = re.match(
            r"^(?P<intro>.+?\b(?:statements?|pairs?|provisions?|features?|countries|crops|rivers|materials)\s*:)\s*(?P<body>.+)$",
            core,
            flags=re.I,
        )
    if not m:
        return None
    intro = m.group("intro").strip()
    body = m.group("body").strip()
    # Don't number if body looks like a single short answer phrase
    if len(body) < 40:
        return None
    # Guard: body should not start with "is/are correct" leftovers
    if re.match(r"^(?:is/are|are|is)\b", body, re.I):
        return None
    # Split into sentences
    protected = re.sub(r"\b([A-Z])\.(?=[A-Z]|\s)", r"\1·", body)
    protected = re.sub(
        r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|No|vol|pp|Art|Rs|U\.S|U\.K)\.",
        lambda mm: mm.group(0).replace(".", "·"),
        protected,
        flags=re.I,
    )
    parts = re.split(r"(?<=[a-z0-9\)\]\"'”'])[.!?][\"'”]?\s+(?=[A-Z\"'“])", protected)
    sents = [p.replace("·", ".").strip() for p in parts if p.strip()]
    # Also try splitting on "; " for semi-list
    if len(sents) < 2:
        sents = [x.strip() for x in re.split(r";\s+", body) if x.strip()]
    if len(sents) < 2 or len(sents) > 8:
        return None
    # Require each "statement" to be substantive
    if any(len(x.split()) < 3 for x in sents):
        # maybe pair lines Name : Place Name : Place without sentence ends
        pairs = re.findall(
            r"([A-Za-z][A-Za-z0-9\s\-\.'’]+?)\s*:\s*([A-Za-z][A-Za-z0-9\s\-\.'’]+?)(?=\s+[A-Z][a-z]|\s*$)",
            body,
        )
        if len(pairs) >= 2:
            lines = [f"{i+1}. {a.strip()} : {b.strip()}" for i, (a, b) in enumerate(pairs)]
            return intro.rstrip(":") + "\n\n" + "\n".join(lines) + select_tail
        return None
    lines = []
    for i, sent in enumerate(sents):
        if sent[-1] not in ".!?":
            sent = sent + "."
        lines.append(f"{i+1}. {sent}")
    return intro.rstrip(":") + "\n\n" + "\n".join(lines) + select_tail



def number_capitalized_name_list(stem: str, options: list | None = None) -> str | None:
    """Number lists of person names split before initials (G. / R. C.)."""
    opts = option_texts(options)
    if not _CODE_OPT_RE.search(opts):
        return None
    if count_numbered_statements(stem or "") >= 2:
        return None
    one = re.sub(r"\s+", " ", stem or "").strip()
    select_m = _SELECT_RE.search(one)
    select_tail = ""
    if select_m:
        select_tail = "\n\n" + select_m.group(1).strip()
        one = one[: select_m.start()].strip()
    m = re.match(r"^(.+\?)\s+(.+)$", one)
    if not m:
        return None
    intro, rest = m.group(1).strip(), m.group(2).strip()
    if not re.search(r"\b(who of the following|which of the following)\b", intro, re.I):
        return None
    # Split before "X. Surname" initials that begin a new person
    parts = re.split(r"(?<=[a-z])\s+(?=[A-Z]\.\s)", rest)
    names = [p.strip(" .,") for p in parts if p.strip()]
    if not (2 <= len(names) <= 6):
        return None
    if any(len(n.split()) > 8 for n in names):
        return None
    lines = [f"{i+1}. {n}" for i, n in enumerate(names)]
    return intro + "\n\n" + "\n".join(lines) + select_tail


def number_consider_following_items(stem: str, options: list | None = None) -> str | None:
    """Number short item lists after 'Consider the following …:' """
    if count_numbered_statements(stem or "") >= 2:
        return None
    one = re.sub(r"\s+", " ", stem or "").strip()
    select_m = _SELECT_RE.search(one)
    select_tail = ""
    if select_m:
        select_tail = "\n\n" + select_m.group(1).strip()
        one = one[: select_m.start()].strip()
    which_m = re.search(r"\s+(Which of the above\b.*)$", one, re.I)
    which_tail = ""
    if which_m:
        which_tail = "\n\n" + which_m.group(1).strip()
        one = one[: which_m.start()].strip()
    m = re.match(
        r"^(?P<intro>Consider the following[^:?]{0,80}:)\s*(?P<body>.+)$",
        one,
        flags=re.I,
    )
    if not m:
        return None
    intro = m.group("intro").strip()
    body = m.group("body").strip()
    # Body should not be long prose sentences
    if len(body) > 220 and body.count(".") >= 2:
        return None
    if "," in body:
        items = [x.strip(" .;") for x in body.split(",") if x.strip()]
    else:
        # Tokenize keeping lowercase continuations with prior Capital token
        # e.g. "Groundnut Sesamum Pearl millet" → 3 items
        toks = body.split()
        items = []
        cur: list[str] = []
        for tok in toks:
            if re.match(r"^[A-Z]", tok) and cur and not re.match(r"^[A-Z]\.$", cur[-1]):
                items.append(" ".join(cur))
                cur = [tok]
            else:
                cur.append(tok)
        if cur:
            items.append(" ".join(cur))
        items = [it.strip(" .;") for it in items if it.strip()]
    if not (2 <= len(items) <= 10):
        return None
    lines = [f"{i+1}. {it}" for i, it in enumerate(items)]
    return intro + "\n\n" + "\n".join(lines) + which_tail + select_tail



def repair_stem(stem: str, options: list | None = None) -> tuple[str, list[str]]:
    """Apply pure repairs; return (new_stem, list of repair tags applied)."""
    applied: list[str] = []
    s = stem or ""
    s2 = fix_pipe_noise(s)
    if s2 != s:
        applied.append("pipe_noise")
        s = s2
    s2 = apply_ocr_token_fixes(s)
    if s2 != s:
        applied.append("ocr_tokens")
        s = s2
    s2 = fix_select_glued(s)
    if s2 != s:
        applied.append("select_glued")
        s = s2
    for fixer, tag in [
        (lambda x: fix_glued_colon_pairs(x), "colon_pairs"),
        (lambda x: fix_inline_numbered_to_multiline(x), "inline_num"),
        (lambda x: fix_unnumbered_items_for_code_options(x, options), "unnumbered"),
        (lambda x: number_statement_sentences(x, options), "stmt_sentences"),
        (lambda x: number_consider_following_items(x, options), "consider_items"),
        (lambda x: number_capitalized_name_list(x, options), "name_list"),
    ]:
        repaired = fixer(s)
        if repaired and repaired != s:
            s = repaired
            applied.append(tag)
            # re-apply select glue after structural change
            s = fix_select_glued(s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s, applied


def scan_bank(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    qs = data.get("questions") or []
    hits = []
    for i, q in enumerate(qs):
        stem = q.get("question") or q.get("stem") or ""
        opts = q.get("options") or []
        scars = high_severity_scars(stem, opts)
        ca = q.get("correctAnswers") or q.get("correct") or []
        if not ca and not (q.get("answer") or {}).get("correct"):
            scars.append("missing_answer")
        if scars:
            hits.append(
                {
                    "index": i + 1,
                    "id": q.get("id"),
                    "scars": scars,
                    "stem_preview": stem[:160].replace("\n", " | "),
                }
            )
    return hits


def scan_all_static(static_dir: Path) -> dict[str, list]:
    out: dict[str, list] = {}
    for f in sorted(static_dir.glob("*.json")):
        out[f.stem] = scan_bank(f)
    return out


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("static/upsc/prelims-gs1")
    results = scan_all_static(root)
    total = 0
    for year, hits in results.items():
        total += len(hits)
        if hits:
            print(f"{year}: {len(hits)} high-severity")
            for h in hits[:5]:
                print(f"  Q{h['index']} {h['scars']}: {h['stem_preview'][:100]}")
    print(f"TOTAL_HIGH_SEVERITY={total}")
    sys.exit(0 if total == 0 else 1)
