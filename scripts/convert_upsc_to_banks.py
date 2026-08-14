#!/usr/bin/env python3
"""Convert UPSC CSE PYQ papers into Loop QuestionBank JSON under static/upsc/."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

# Prefer the full Desktop LOOP DATA workspace when present (authoritative).
# Fall back to a local ./LOOP DATA checkout for CI/portable runs.
_DESKTOP_SRC = Path("/Users/pradheepvijayaraj/Desktop/LOOP DATA/PYQ/UPSC/CSE")
_LOCAL_SRC = Path("LOOP DATA/PYQ/UPSC/CSE")
SRC = _DESKTOP_SRC if _DESKTOP_SRC.exists() else _LOCAL_SRC
OUT = Path("static/upsc")

# Bump when conversion output shape changes so the app can re-seed.
CONTENT_VERSION = 45

# SuperKalam CSAT figures shipped under static/upsc/assets/csat/
_CSAT_ASSET_DIR = "upsc/assets/csat"
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)]+|/?upsc/assets/[^)]+)\)")


def _optional_meta(title: str, section: str) -> dict:
    """Shared defaults for UPSC CSE optional theory papers (250 max; 50/Q)."""
    return {
        "title": title,
        "section": section,
        "default_duration": 10800,  # 3 hours
        "difficulty": "hard",
        # 5 questions attempted × 50 = 250 max marks (standard UPSC optional)
        "marks": 50.0,
        "negative": 0.0,
        "mode": "descriptive",
        "optional": True,
    }


PAPER_META = {
    ("PRELIMS", "GS1"): {
        "title": "Prelims GS Paper I",
        "section": "prelims-gs1",
        "default_duration": 7200,
        "difficulty": "hard",
        "marks": 2.0,
        "negative": round(2.0 / 3.0, 3),  # 0.667 — UPSC −⅓ of marks
        "mode": "mcq",
    },
    ("PRELIMS", "CSAT"): {
        "title": "Prelims CSAT (GS Paper II)",
        "section": "prelims-csat",
        "default_duration": 7200,  # 2 hours
        "difficulty": "hard",
        "marks": 2.5,
        "negative": round(2.5 / 3.0, 3),  # 0.833 — UPSC −⅓ of marks
        "mode": "mcq",
    },
    ("MAINS", "ESSAY"): {
        "title": "Mains Essay",
        "section": "mains-essay",
        "default_duration": 10800,
        "difficulty": "hard",
        "marks": 125.0,
        "negative": 0.0,
        "mode": "descriptive",
    },
    ("MAINS", "GS1"): {
        "title": "Mains GS Paper I",
        "section": "mains-gs1",
        "default_duration": 10800,
        "difficulty": "hard",
        "marks": 10.0,
        "negative": 0.0,
        "mode": "descriptive",
    },
    ("MAINS", "GS2"): {
        "title": "Mains GS Paper II",
        "section": "mains-gs2",
        "default_duration": 10800,
        "difficulty": "hard",
        "marks": 10.0,
        "negative": 0.0,
        "mode": "descriptive",
    },
    ("MAINS", "GS3"): {
        "title": "Mains GS Paper III",
        "section": "mains-gs3",
        "default_duration": 10800,
        "difficulty": "hard",
        "marks": 10.0,
        "negative": 0.0,
        "mode": "descriptive",
    },
    ("MAINS", "GS4"): {
        "title": "Mains GS Paper IV",
        "section": "mains-gs4",
        "default_duration": 10800,
        "difficulty": "hard",
        "marks": 10.0,
        "negative": 0.0,
        "mode": "descriptive",
    },
    # --- Optionals (famous set in Desktop LOOP DATA) ---
    ("MAINS", "MATHS1"): _optional_meta(
        "Mathematics Optional Paper I", "mains-maths1"
    ),
    ("MAINS", "MATHS2"): _optional_meta(
        "Mathematics Optional Paper II", "mains-maths2"
    ),
    ("MAINS", "ANTHROPOLOGY1"): _optional_meta(
        "Anthropology Optional Paper I", "mains-anthropology1"
    ),
    ("MAINS", "ANTHROPOLOGY2"): _optional_meta(
        "Anthropology Optional Paper II", "mains-anthropology2"
    ),
    ("MAINS", "GEOGRAPHY1"): _optional_meta(
        "Geography Optional Paper I", "mains-geography1"
    ),
    ("MAINS", "GEOGRAPHY2"): _optional_meta(
        "Geography Optional Paper II", "mains-geography2"
    ),
    ("MAINS", "HISTORY1"): _optional_meta(
        "History Optional Paper I", "mains-history1"
    ),
    ("MAINS", "HISTORY2"): _optional_meta(
        "History Optional Paper II", "mains-history2"
    ),
    ("MAINS", "PSIR1"): _optional_meta(
        "PSIR Optional Paper I", "mains-psir1"
    ),
    ("MAINS", "PSIR2"): _optional_meta(
        "PSIR Optional Paper II", "mains-psir2"
    ),
    ("MAINS", "PUBAD1"): _optional_meta(
        "Public Administration Optional Paper I", "mains-pubad1"
    ),
    ("MAINS", "PUBAD2"): _optional_meta(
        "Public Administration Optional Paper II", "mains-pubad2"
    ),
    ("MAINS", "SOCIOLOGY1"): _optional_meta(
        "Sociology Optional Paper I", "mains-sociology1"
    ),
    ("MAINS", "SOCIOLOGY2"): _optional_meta(
        "Sociology Optional Paper II", "mains-sociology2"
    ),
    ("MAINS", "ECONOMICS1"): _optional_meta(
        "Economics Optional Paper I", "mains-economics1"
    ),
    ("MAINS", "ECONOMICS2"): _optional_meta(
        "Economics Optional Paper II", "mains-economics2"
    ),
    ("MAINS", "PHILOSOPHY1"): _optional_meta(
        "Philosophy Optional Paper I", "mains-philosophy1"
    ),
    ("MAINS", "PHILOSOPHY2"): _optional_meta(
        "Philosophy Optional Paper II", "mains-philosophy2"
    ),
}


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def localize_csat_images(text: str) -> str:
    """
    Rewrite SuperKalam CloudFront markdown images to bundled app paths.
    Also strip $ from alt text so KaTeX does not eat option figure alts like ![$57A$](…).
    """
    if not text or "![" not in text:
        return text

    def repl(m: re.Match[str]) -> str:
        alt = (m.group(1) or "").replace("$", "").strip() or "Figure"
        url = m.group(2) or ""
        name = url.rstrip("/").split("/")[-1]
        if not name or "." not in name:
            return m.group(0)
        return f"![{alt}](/{_CSAT_ASSET_DIR}/{name})"

    return _MD_IMAGE_RE.sub(repl, text)


_SIMPLE_MATH_RE = re.compile(r"\$([+-]?\d+(?:\.\d+)?)\$")


def unwrap_simple_math(text: str) -> str:
    """$7$ / $16$ / $48.1$ → plain digits so UI uses body font, not KaTeX."""
    if not text or "$" not in text:
        return text
    return _SIMPLE_MATH_RE.sub(r"\1", text)


def clean_csat_stem_markers(text: str) -> str:
    """Remove SuperKalam list stubs: '1. ![fig]', bare '1.' lines above figures."""
    if not text:
        return text
    text = re.sub(r"(?m)^\s*\d+\.\s*(?=!\[)", "", text)
    text = re.sub(r"(?m)^\s*\d+\.\s*\n(?=\s*!\[)", "", text)
    # Drop orphan numbered lines that are only "1." / "2."
    text = re.sub(r"(?m)^\s*\d+\.\s*$", "", text)
    return text


def build_csat_stem(q: dict) -> str:
    """
    CSAT: keep booklet stem + shared passage; do NOT run GS findings/list normalizers
    (those turn '![](url)' into '1. ![](url)' and break figures).
    """
    passage = clean_text(str(q.get("shared_passage") or ""))
    flat = clean_text(q.get("question") or "")
    # Prefer flat string (already has markdown images). Fall back to light content join.
    if not flat:
        parts: list[str] = []
        for block in q.get("content") or []:
            t = clean_text(block.get("text") or "")
            if t:
                parts.append(t)
        flat = "\n\n".join(parts)
    stem = flat
    if passage and passage[:50] not in stem:
        stem = f"{passage}\n\n{stem}" if stem else passage
    stem = localize_csat_images(stem)
    stem = clean_csat_stem_markers(stem)
    stem = unwrap_simple_math(stem)
    stem = re.sub(r"\n{3,}", "\n\n", stem).strip()
    return stem


# ---------------------------------------------------------------------------
# Descriptive (GS / Essay) source cleanup — LOOP DATA is OCR-noisy:
# glued marks, bilingual garble prefixes, merged questions, word-limit noise.
# ---------------------------------------------------------------------------

_WORD_LIMIT_RE = re.compile(
    r"""
    \s*
    (?:
        \(\s*Answer\s+in\s+\d+\s*words?\s*\)
      | \(\s*\d+\s*words?\s*\)
      | \(\s*\d{2,3}\s+\d{2,3}\s*\)          # OCR of "(150  words)" → "(150 316)"
      | \(\s*Sa\s+\d+[^)]*\)                 # OCR of "(Sa 250 ...)"
      | \(\s*om\s+\d+[^)]*\)                 # OCR of "(om 150 ...)"
      | \(\s*250\s+Beal[^)]*\)
    )
    """,
    re.I | re.X,
)

_ANSWER_IN_WORDS_RE = re.compile(
    r"\s*Answer\s+in\s+\d+\s*words\.?", re.I
)

# Trailing UPSC marks tags (10 / 15 / 20), often glued: "Elucidate.10"
_TRAILING_MARKS_RE = re.compile(
    r"(?:[.]\s*)?(?<![\d])(10|15|20)\s*$"
)

# English question body openers (after optional OCR garbage prefix).
# Avoid bare "A"/"An" — they false-match OCR crumbs like "A ore we".
_ENGLISH_BODY_RE = re.compile(
    r"(?P<body>"
    r"(?:Discuss|Examine|Explain|Comment|Trace|Highlight|Evaluate|Critically|"
    r"Analyze|Analyse|Elucidate|Describe|Compare|Account|Bring|Distinguish|"
    r"Whether|Write|Enumerate|How|What|Why|Give|Does\b|Do\s|Is\s|Are\s|"
    r"The\s+[A-Za-z]{3,}|"
    r"In\s+the\b|To\s+what\b|With\s+reference\b|"
    r"[‘'\"“])"
    r"[\s\S]{12,})",
    re.I,
)

_NEXT_Q_OPENER = (
    r"Discuss|Examine|Explain|Comment|Trace|Highlight|Evaluate|Critically|"
    r"Analyze|Analyse|Elucidate|Describe|Compare|How|What|Why|Give|Does|Do|"
    r"Is|Are|The|‘|\"|“"
)

# High-confidence OCR typos seen in GS sources
_OCR_FIXES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bthé\b", re.I), "the"),
    (re.compile(r"Harapphey\s+bfGhitebture", re.I), "Harappan architecture"),
    (re.compile(r"\bHarapphey\b", re.I), "Harappan"),
    (re.compile(r"\bbfGhitebture\b", re.I), "architecture"),
    (re.compile(r"\bGhit\s*ebture\b", re.I), "architecture"),
]


def _english_token_ratio(text: str) -> float:
    tokens = re.findall(r"[A-Za-z]+", text)
    if not tokens:
        return 0.0
    # Real English words tend to be longer and dictionary-ish; use length heuristic
    good = sum(1 for t in tokens if len(t) >= 4)
    return good / len(tokens)


def _looks_like_ocr_garbage(prefix: str) -> bool:
    if not prefix or not prefix.strip():
        return False
    if re.search(r"[\u0900-\u097F@¥]", prefix):
        return True
    if re.search(r"\b(wet wet|stk fewer|bfGh|Harapphey)\b", prefix, re.I):
        return True
    tokens = re.findall(r"[A-Za-z]+", prefix)
    if len(tokens) >= 4:
        short = sum(1 for t in tokens if len(t) <= 3)
        if short / len(tokens) >= 0.55:
            return True
    if len(prefix) > 20 and _english_token_ratio(prefix) < 0.35:
        return True
    return False


def strip_ocr_garbage_prefix(text: str) -> str:
    """Drop bilingual/OCR junk that precedes the real English question."""
    text = text.strip()
    if not text:
        return text

    # Pipe-separated bilingual OCR: "hindi junk | The Bhakti movement..."
    if "|" in text:
        left, right = text.rsplit("|", 1)
        right = right.strip()
        if right and _looks_like_ocr_garbage(left) and _ENGLISH_BODY_RE.match(right):
            text = right

    # Prefer the first opener whose left side looks like garbage (or start)
    for m in _ENGLISH_BODY_RE.finditer(text):
        start = m.start("body")
        if start <= 0:
            return m.group("body").lstrip()
        prefix = text[:start]
        if _looks_like_ocr_garbage(prefix):
            return m.group("body").lstrip()
    return text


def apply_ocr_fixes(text: str) -> str:
    for pat, rep in _OCR_FIXES:
        text = pat.sub(rep, text)
    return text


def peel_trailing_marks(text: str) -> tuple[str, float | None]:
    """Return (text_without_trailing_marks, marks_or_None)."""
    text = text.rstrip()
    m = _TRAILING_MARKS_RE.search(text)
    if m:
        return text[: m.start()].rstrip(" ."), float(m.group(1))
    # Glued without separator: "Elucidate10"
    m2 = re.search(r"([A-Za-z)'”’\.])(10|15|20)\s*$", text)
    if m2:
        return text[: m2.start(2)].rstrip(), float(m2.group(2))
    return text, None


def split_merged_descriptive(text: str) -> list[tuple[str, float | None]]:
    """
    Split stems that glued two UPSC questions via trailing marks:
      "...examples.10\\nWhat are Tsunamis? ...10"
    """
    text = clean_text(text)
    if not text:
        return []

    # Split after marks when another question clearly begins
    splitter = re.compile(
        rf"(?<=[A-Za-z.?!)'\"”’])\s*(10|15|20)\s*(?=(?:\n+\s*|(?={_NEXT_Q_OPENER})))",
        re.I,
    )
    pieces: list[str] = []
    marks_list: list[float | None] = []
    last = 0
    for m in splitter.finditer(text):
        chunk = text[last : m.start()].strip()
        if chunk:
            pieces.append(chunk)
            marks_list.append(float(m.group(1)))
        last = m.end()
    tail = text[last:].strip()
    if tail:
        # Tail may still have trailing marks
        tail_clean, tail_marks = peel_trailing_marks(tail)
        if tail_clean:
            pieces.append(tail_clean)
            marks_list.append(tail_marks)

    if not pieces:
        cleaned, marks = peel_trailing_marks(text)
        return [(cleaned, marks)] if cleaned else []

    # If splitter never fired but we only got one piece from logic above
    if len(pieces) == 1 and marks_list[0] is None:
        cleaned, marks = peel_trailing_marks(pieces[0])
        return [(cleaned, marks)] if cleaned else []

    out: list[tuple[str, float | None]] = []
    for chunk, mk in zip(pieces, marks_list):
        chunk2, mk2 = peel_trailing_marks(chunk)
        out.append((chunk2, mk if mk is not None else mk2))
    return [(c, m) for c, m in out if c]


def _is_viable_descriptive_stem(stem: str) -> bool:
    """Reject OCR fragments left after bad splits (e.g. 'of the world. How…')."""
    s = stem.strip()
    if len(s) < 28:
        return False
    # Must look like a real question start
    if not re.match(r"^[A-Z(‘'\"“0-9]", s):
        return False
    # Leading fragment of a longer sentence
    if re.match(
        r"^(of|and|or|to|in|for|with|from|on|at|by|as|that|which|who)\b",
        s,
        re.I,
    ):
        return False
    # Mostly non-Latin / symbols
    letters = sum(1 for c in s if c.isalpha())
    if letters < 20:
        return False
    # Unrecoverable OCR with little real English
    if _english_token_ratio(s) < 0.28 and (
        _looks_like_ocr_garbage(s[:100]) or re.search(r"[\u0900-\u097F@¥]", s)
    ):
        return False
    return True


def clean_descriptive_units(
    text: str, default_marks: float
) -> list[tuple[str, float]]:
    """
    Full descriptive cleanup → one or more (stem, marks) units.
    """
    text = clean_text(text)
    text = _WORD_LIMIT_RE.sub("", text)
    text = _ANSWER_IN_WORDS_RE.sub("", text)
    text = clean_text(text)

    units = split_merged_descriptive(text)
    cleaned: list[tuple[str, float]] = []
    for stem, marks in units:
        stem = strip_ocr_garbage_prefix(stem)
        stem = apply_ocr_fixes(stem)
        stem = clean_text(stem)
        # Drop residual leading punctuation junk
        stem = re.sub(r"^[\s|.,;:–—-]+", "", stem)
        if not _is_viable_descriptive_stem(stem):
            continue
        cleaned.append((stem, float(marks) if marks is not None else default_marks))
    return cleaned


def item_label(item: dict, index: int, numbering: str | None) -> str:
    raw = str(item.get("label") or item.get("id") or "").strip()
    if raw:
        return raw
    # Roman-style if source used statement numbering with I, II…
    if numbering == "statement":
        romans = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        if 0 <= index < len(romans):
            return romans[index]
    return str(index + 1)


def format_items_block(block: dict) -> str:
    numbering = block.get("numbering")
    items = block.get("items") or []
    lines: list[str] = []
    for i, item in enumerate(items):
        label = item_label(item, i, numbering)
        body = clean_text(item.get("text") or "")
        if not body:
            continue
        # Avoid double-prefix if body already starts with the label
        if re.match(rf"^{re.escape(label)}[\).:\s]", body):
            lines.append(body)
        else:
            lines.append(f"{label}. {body}")
    return "\n".join(lines)


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    # Protect initials (M.N. Roy) and common abbreviations so we don't split on them.
    protected = re.sub(r"\b([A-Z])\.(?=[A-Z]|\s)", r"\1·", text)
    protected = re.sub(
        r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|No|vol|pp)\.",
        lambda m: m.group(0).replace(".", "·"),
        protected,
        flags=re.IGNORECASE,
    )
    # Split only after sentence-ending punctuation following a word char (not an initial).
    parts = re.split(r"(?<=[a-z0-9\)\]\"'])[.!?][\"']?\s+(?=[A-Z\"'])", protected)
    return [p.replace("·", ".").strip() for p in parts if p.strip()]


def _already_numbered_list(body: str) -> bool:
    """True if body already has ≥2 numbered list items (1. / 1) style)."""
    items = re.findall(r"(?m)^\s*(?:\d+|I{1,3}|IV|V)[\.)]\s+\S", body)
    if len(items) >= 2:
        return True
    # also accept compact "1. foo 2. bar" without newlines when clearly listed
    compact = re.findall(r"(?:^|\s)(?:\d+|I{1,3}|IV|V)[\.)]\s+\S", body)
    return len(compact) >= 2


def _is_assertion_reason_stem(body: str) -> bool:
    """Statement-I / Statement-II assertion–reason stems must pass through untouched.

    number_body_sentences previously rewrote these into:
      1. Statement-I: …
      2. Statement-II: …
      3. Which one of the following is correct…
    which is garbage (prompt-as-item) and breaks inventory gates.
    """
    if not body:
        return False
    return bool(
        re.search(r"(?i)\bStatement[- ]?(?:I|1)\b", body)
        and re.search(r"(?i)\bStatement[- ]?(?:II|2)\b", body)
    )


def number_body_sentences(body: str) -> str:
    """Turn a run of sentences into a numbered list (1. …)."""
    body = clean_text(body)
    # Never re-number stems that already expose a UPSC-style list — doing so
    # splits on "1. Vitasta : Chenab" (period after the index) and produces garbage.
    if _already_numbered_list(body):
        return body
    # Never re-number clean Statement-I / Statement-II assertion–reason stems.
    if _is_assertion_reason_stem(body):
        return body
    sentences = split_sentences(body)
    if len(sentences) < 2:
        return body
    return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))


def format_code_style_paragraph(text: str) -> str | None:
    """
    Pattern: <intro ending ?> <factor sentences> Select the answer using the code…
    Common in UPSC when content[] never split the list.
    """
    text = clean_text(text)
    # Already well-structured: keep as-is (only normalize blank lines)
    if _already_numbered_list(text) and re.search(
        r"Select the answer using the code", text, re.I
    ):
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    match = re.match(
        r"^(?P<intro>.+\?)\s+(?P<body>.+?)\s+(?P<select>Select the answer using the code given below\.?)\s*$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    intro = clean_text(match.group("intro"))
    body = clean_text(match.group("body"))
    select = clean_text(match.group("select"))
    if _already_numbered_list(body):
        # Preserve existing numbering; ensure items are on separate lines
        body_fmt = re.sub(
            r"(?<!\n)\s+(?=(?:\d+|I{1,3}|IV|V)[\.)]\s+)", "\n", body
        ).strip()
        return f"{intro}\n\n{body_fmt}\n\n{select}"
    numbered = number_body_sentences(body)
    if numbered == body and "\n" not in numbered:
        return None
    return f"{intro}\n\n{numbered}\n\n{select}"

def normalize_mixed_markers(findings: str) -> str:
    """
    Handle blobs like:
      Sentence one. Sentence two. III. Sentence three.
    → numbered 1/2 then keep III, or renumber all 1/2/3.
    """
    findings = clean_text(findings)
    findings = re.sub(r"(?<!\n)\s+((?:I{1,3}|IV|V|\d+)\.)\s+", r"\n\1 ", findings)
    lines = [ln.strip() for ln in findings.split("\n") if ln.strip()]
    if not lines:
        return findings

    out: list[str] = []
    pending: list[str] = []
    for line in lines:
        if re.match(r"^(?:\d+|I{1,3}|IV|V)\.\s+", line):
            if pending:
                out.extend(
                    f"{i + 1}. {s}" for i, s in enumerate(split_sentences(" ".join(pending)))
                )
                pending = []
            # peel "Select the answer…" glued onto last item
            line = re.sub(
                r"\s+(Select the answer using the code given below\.?)\s*$",
                "",
                line,
                flags=re.IGNORECASE,
            )
            out.append(line)
        else:
            pending.append(line)
    if pending:
        out.extend(f"{i + 1}. {s}" for i, s in enumerate(split_sentences(" ".join(pending))))
    # Normalize labels to 1..n so mixed "1. / III." sources read cleanly
    renumbered: list[str] = []
    for i, line in enumerate(out):
        body = re.sub(r"^(?:\d+|I{1,3}|IV|V)\.\s*", "", line).strip()
        if not body:
            continue
        # restore terminal period if sentence lost it during splits —
        # but not for pair/match lines ("Vitasta : Chenab") or fragments
        if body[-1] not in ".!?" and ":" not in body and len(body.split()) >= 5:
            body = body + "."
        renumbered.append(f"{i + 1}. {body}")
    return "\n".join(renumbered)


def normalize_findings_paragraph(text: str) -> str:
    """Break smashed findings that only label some items (e.g. mid-text 'III.')."""
    text = clean_text(text)
    # Newline before roman / arabic list markers
    text = re.sub(r"(?<!\n)\s+((?:I{1,3}|IV|V|\d+)\.)\s+", r"\n\1 ", text)
    # Split "topic: sentence. sentence." into topic + numbered sentences when possible
    colon = re.match(
        r"^(?P<head>.+?:)\s+(?P<body>.+)$",
        text,
        flags=re.DOTALL,
    )
    if colon:
        head = clean_text(colon.group("head"))
        body = clean_text(colon.group("body"))
        # Pull trailing question out of body if present
        q_split = re.split(
            r"(?=\bWhich of the following\b)",
            body,
            maxsplit=1,
            flags=re.IGNORECASE,
        )
        findings = q_split[0].strip()
        tail = q_split[1].strip() if len(q_split) > 1 else ""
        findings_fmt = normalize_mixed_markers(findings)
        parts = [head, findings_fmt]
        if tail:
            parts.append(tail)
        return "\n\n".join(p for p in parts if p)
    return text


def stem_from_content(content: list | None) -> str:
    if not content:
        return ""

    has_list_block = any(
        b.get("type") in ("list", "statements", "sequence") for b in content
    )
    parts: list[str] = []
    statement_labels: set[str] = set()

    for block in content:
        btype = block.get("type")
        if btype == "paragraph":
            text = clean_text(block.get("text") or "")
            if not text:
                continue
            # Prefer code-style split when paragraph alone holds the whole item list
            if not has_list_block:
                code_fmt = format_code_style_paragraph(text)
                if code_fmt:
                    parts.append(code_fmt)
                    continue
            text = normalize_findings_paragraph(text)
            # If we also have a statements/list block, strip a trailing prompt
            # that will be re-added later (avoids mega-duplication).
            if has_list_block:
                text = re.split(
                    r"\bWhich of the following\b",
                    text,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()
                text = re.sub(
                    r"\s*Consider the following statements with reference to the above\s*:?\s*$",
                    "\n\nConsider the following statements with reference to the above:",
                    text,
                    flags=re.IGNORECASE,
                ).strip()
            if text:
                parts.append(text)
        elif btype in ("list", "statements", "sequence"):
            for item in block.get("items") or []:
                statement_labels.add(str(item.get("label") or item.get("id") or ""))
            formatted = format_items_block(block)
            # Incomplete fragments like "suggests that…" → "I. Statement I suggests…"
            if block.get("numbering") == "statement":
                fixed_lines = []
                for line in formatted.split("\n"):
                    line = re.sub(
                        r"\s+(Select the answer using the code given below\.?)\s*$",
                        "",
                        line,
                        flags=re.IGNORECASE,
                    )
                    m = re.match(r"^([IVX\d]+)\.\s+(suggests\b.*)$", line, re.I)
                    if m:
                        fixed_lines.append(
                            f"{m.group(1)}. Statement {m.group(1)} {m.group(2)}"
                        )
                    else:
                        fixed_lines.append(line)
                formatted = "\n".join(fixed_lines)
            if formatted:
                parts.append(formatted)
        elif btype == "prompt":
            text = clean_text(block.get("text") or "")
            if not text:
                continue
            # Drop prompt that re-dumps all Statement I/II/III prose
            if statement_labels and text.lower().count("statement") >= 2:
                select = re.search(
                    r"(Select the answer using the code given below\.?)",
                    text,
                    flags=re.IGNORECASE,
                )
                which = re.search(
                    r"(Which of the following[^.?]*[.?])",
                    text,
                    flags=re.IGNORECASE,
                )
                short_bits = []
                if which:
                    short_bits.append(which.group(1).strip())
                if select:
                    short_bits.append(select.group(1).strip())
                text = "\n\n".join(short_bits) if short_bits else text
            if text:
                parts.append(text)
        elif btype == "match":
            left = block.get("left") or block.get("items") or []
            if isinstance(left, list):
                formatted = format_items_block({"numbering": "none", "items": left})
                if formatted:
                    parts.append(formatted)
            text = clean_text(block.get("text") or "")
            if text:
                parts.append(text)
        else:
            text = clean_text(block.get("text") or "")
            if text:
                parts.append(text)

    return "\n\n".join(parts).strip()


def improve_flat_stem(flat: str) -> str:
    """Best-effort formatting when structured content is missing/poor."""
    text = clean_text(flat)
    if not text:
        return text

    code_fmt = format_code_style_paragraph(text)
    if code_fmt:
        return code_fmt

    text = normalize_findings_paragraph(text)

    # Insert newlines before "Statement I/II/III" if smashed into prose
    text = re.sub(
        r"(?<!\n)\s*(Statement\s+(?:I{1,3}|IV|V|1|2|3|4)\b)",
        r"\n\n\1",
        text,
        flags=re.IGNORECASE,
    )
    # "Select the answer using the code given below" as its own line
    text = re.sub(
        r"(?<!\n)\s*(Select the answer using the code given below\.?)",
        r"\n\n\1",
        text,
        flags=re.IGNORECASE,
    )
    # "Which of the following" after a long period as break for multi-part
    text = re.sub(
        r"(?<=[.?!])\s+(Which of the following)",
        r"\n\n\1",
        text,
    )

    return clean_text(text)


def _map_outside_math(text: str, fn) -> str:
    """Apply fn only outside $...$ / $$...$$ so LaTeX is never split."""
    parts = re.split(r"(\$\$[\s\S]+?\$\$|\$[^$]+\$)", text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            out.append(fn(part))
    return "".join(out)


def format_multipart_stem(text: str) -> str:
    """
    Preserve multi-part theory stems: (a)/(b)/(c) and (i)/(ii)/(iii) on their own lines.
    Aligns "(c) (i) … / (ii) …" and "for (i) … / (ii) …".
    Do NOT run prelims-oriented finders (they mangle LaTeX / matrices).
    """
    text = clean_text(text)
    if not text:
        return text

    def transform(plain: str) -> str:
        # Keep "(a)(i)" on the same line as the letter
        plain = re.sub(r"(\([a-e]\))\s*(\(i\))", r"\1 \2", plain, flags=re.I)
        # Later glued subs "(a)(ii)" → own line
        plain = re.sub(
            r"(\([a-e]\))\s*(\((?:ii|iii|iv|II|III|IV)\))",
            r"\n\2",
            plain,
        )
        # Major parts (a)-(e)
        plain = re.sub(r"(?<!\n)\s+(\([a-e]\))\s+", r"\n\1 ", plain)
        # Later roman only — do not peel (i) off the letter line
        plain = re.sub(r"\s+(\((?:ii|iii|iv|II|III|IV)\))\s+", r"\n\1 ", plain)
        # (I)/(II)/(III) after semicolon
        plain = re.sub(r";\s*(\([IVX]+\))\s*", r"\n\1 ", plain)
        # Drop dangling "and"/"or" before a sub-part line
        plain = re.sub(r";?\s+\b(?:and|or)\s*(?=\n\()", "", plain, flags=re.I)
        return plain

    text = _map_outside_math(text, transform)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_latex_heavy(text: str) -> bool:
    return bool(
        re.search(
            r"\$|\\begin\{|\\mathbb|\\frac|\\int|\\sum|\\partial|\\nabla",
            text or "",
        )
    )


def build_stem(q: dict) -> str:
    flat_raw = q.get("question") or ""
    content = q.get("content") or []
    passage = clean_text(str(q.get("shared_passage") or ""))

    def with_passage(stem: str) -> str:
        stem = clean_text(stem)
        if not passage:
            return stem
        if not stem:
            return passage
        # Don't double-prefix if the stem already embeds the passage
        if passage[:60] and passage[:60] in stem:
            return stem
        return f"{passage}\n\n{stem}"

    # Multi-part / LaTeX theory stems: use the flat question field only.
    # stem_from_content + normalize_findings_paragraph mangles matrices
    # (e.g. inserts "1." and glues (b)/(c) onto one line).
    if re.match(r"^\([a-e]\)", flat_raw.strip()) or is_latex_heavy(flat_raw):
        return with_passage(format_multipart_stem(flat_raw))

    flat = clean_text(flat_raw)
    # Prefer already-clean flat stems with numbered lists (source repairs).
    if flat and _already_numbered_list(flat):
        # Light pass: ensure "Select the answer…" is not glued into last item
        flat = re.sub(
            r"(?m)([^\n])\s+(Select the (?:answer|correct)[^\n]*)$",
            r"\1\n\n\2",
            flat,
            flags=re.I,
        )
        return with_passage(re.sub(r"\n{3,}", "\n\n", flat).strip())

    # Assertion–reason (Statement-I / Statement-II): pass through flat stem.
    # Never route through improve_flat_stem / sentence renumbering.
    if flat and _is_assertion_reason_stem(flat):
        return with_passage(re.sub(r"\n{3,}", "\n\n", flat).strip())

    from_content = stem_from_content(content)

    has_structure = any(
        b.get("type") in ("list", "statements", "sequence", "match") for b in content
    )
    if from_content and (
        has_structure or len(content) > 1 or len(from_content) >= len(flat) * 0.5
    ):
        return with_passage(from_content)

    if flat:
        return with_passage(improve_flat_stem(flat))
    return with_passage(from_content)

def question_tags(meta: dict, q: dict) -> list[str]:
    tags = [meta["title"]]
    if meta["mode"] == "descriptive":
        tags.append("descriptive")
    # UPSC essay / maths: section A or B (choose from each section)
    paper_section = q.get("section")
    if paper_section is not None and str(paper_section).strip() != "":
        tags.append(f"Section {str(paper_section).strip().upper()}")
    # CSAT subject buckets from SuperKalam (comprehension / reasoning / maths)
    subject = q.get("subject")
    if subject is not None and str(subject).strip():
        tags.append(str(subject).strip().lower())
    return tags


def convert_question(q: dict, paper_id: str, meta: dict, number: int) -> list[dict]:
    """
    Convert one source question into one or more bank questions.
    Descriptive GS items may expand when source merged two PYQs.
    """
    tags = question_tags(meta, q)
    ans = q.get("answer") or {}
    correct = list(ans.get("correct") or [])
    options_in = q.get("options") or []

    if meta["mode"] == "mcq" and options_in and correct:
        # Pass-through: never run OCR/scar surgery on prelims stems.
        # Quality is enforced at source (LOOP DATA paper.json) + inventory gate.
        is_csat = str(meta.get("section") or "") == "prelims-csat"
        if is_csat:
            stem = build_csat_stem(q) or f"Question {number}"
        else:
            stem = build_stem(q) or f"Question {number}"
            # Light formatting only: unglue Select-line from last numbered item
            if _already_numbered_list(stem):
                stem = re.sub(
                    r"(?m)([^\n])[ \t]+(Select the (?:answer|correct)[^\n]*)$",
                    r"\1\n\n\2",
                    stem,
                    flags=re.I,
                )
                stem = re.sub(r"\n{3,}", "\n\n", stem).strip()
        qid = f"{paper_id}_q{number}"
        options = []
        id_map: dict[str, str] = {}
        for opt in options_in:
            raw_id = str(opt.get("id", "")).strip()
            new_id = raw_id.lower() if raw_id else raw_id
            id_map[raw_id] = new_id
            id_map[raw_id.upper()] = new_id
            id_map[raw_id.lower()] = new_id
            opt_text = clean_text(opt.get("text") or "") or new_id
            opt_text = opt_text.replace("&#8216;", "'").replace("&#8217;", "'")
            if is_csat:
                opt_text = localize_csat_images(opt_text)
                opt_text = unwrap_simple_math(opt_text)
            options.append({"id": new_id, "text": opt_text})
        mapped_correct = [
            id_map.get(str(c).strip(), str(c).strip().lower()) for c in correct
        ]
        explanation = clean_text(str(q.get("explanation") or ""))
        return [
            {
                "id": qid,
                "type": "single-choice",
                "question": stem,
                "options": options,
                "correctAnswers": mapped_correct,
                "explanation": explanation,
                "marks": meta["marks"],
                "negativeMarks": meta["negative"],
                "negativeMarksUnanswered": 0,
                "difficulty": meta["difficulty"],
                "tags": tags,
            }
        ]

    # Descriptive GS/Essay: clean OCR/glued marks; split merged PYQs.
    # Prefer explicit marks on the source question when present (production GS rebuild).
    source_marks = q.get("marks")
    try:
        source_marks_f = float(source_marks) if source_marks is not None else None
    except (TypeError, ValueError):
        source_marks_f = None
    default_m = source_marks_f if source_marks_f and source_marks_f > 0 else meta["marks"]

    # Optionals (incl. maths): keep multi-part booklet structure intact.
    # GS-style clean_descriptive_units would wrongly split 10×5 short notes.
    is_optional = bool(meta.get("optional")) or str(meta.get("section") or "").startswith(
        "mains-maths"
    )
    if is_optional:
        # Prefer flat booklet stem; content[] is usually a single paragraph copy.
        flat = clean_text(q.get("question") or "")
        raw_stem = format_multipart_stem(flat) if flat else (build_stem(q) or "")
    else:
        raw_stem = build_stem(q) or ""
    conf = q.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else 0.0
    except (TypeError, ValueError):
        conf_f = 0.0

    # High-confidence production rebuild stems: light clean only (don't drop/split)
    if (
        meta["mode"] == "descriptive"
        and not is_optional
        and conf_f >= 0.9
        and raw_stem.strip()
    ):
        stem = clean_text(raw_stem)
        stem = _WORD_LIMIT_RE.sub("", stem)
        stem = _ANSWER_IN_WORDS_RE.sub("", stem)
        stem, peeled = peel_trailing_marks(stem)
        stem = apply_ocr_fixes(stem)
        stem = clean_text(stem)
        units = [(stem, source_marks_f or peeled or default_m)] if len(stem) >= 20 else []
    elif (
        meta["mode"] == "descriptive"
        and not is_optional
        and not is_latex_heavy(raw_stem)
        and not re.match(r"^\([a-e]\)", raw_stem.strip())
    ):
        units = clean_descriptive_units(raw_stem, default_m)
        if len(units) == 1 and source_marks_f and source_marks_f > 0:
            units = [(units[0][0], source_marks_f)]
    else:
        # Optionals / maths / already multipart: light format only
        stem = format_multipart_stem(raw_stem) if raw_stem.strip() else ""
        if is_optional and stem:
            stem = apply_ocr_fixes(stem)
            stem = clean_text(stem)
        units = [(stem, default_m)] if stem else []

    # Unrecoverable OCR / empty after cleanup — drop rather than emit placeholders
    if not units:
        return []

    out: list[dict] = []
    for i, (stem, marks) in enumerate(units):
        qid = (
            f"{paper_id}_q{number}"
            if i == 0
            else f"{paper_id}_q{number}_{i + 1}"
        )
        out.append(
            {
                "id": qid,
                "type": "fill-blank",
                "question": stem,
                "correctAnswers": ["__open__"],
                "explanation": "Open-ended practice. No model answer in this build.",
                "marks": marks,
                "negativeMarks": 0,
                "negativeMarksUnanswered": 0,
                "difficulty": meta["difficulty"],
                "tags": tags,
            }
        )
    return out


def convert_paper(path: Path) -> dict | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    paper = data["paper"]
    stage = path.parts[-4]
    paper_code = path.parts[-3]
    year = int(path.parts[-2]) if path.parts[-2].isdigit() else paper.get("year")
    key = (stage, paper_code)
    if key not in PAPER_META:
        return None
    meta = PAPER_META[key]
    paper_id = paper.get("id") or f"upsc_{year}_{stage.lower()}_{paper_code.lower()}"

    questions: list[dict] = []
    for q in data.get("questions") or []:
        number = int(q.get("number") or (len(questions) + 1))
        questions.extend(convert_question(q, paper_id, meta, number))

    # Stable sequential ids after merge-splits
    renumbered: list[dict] = []
    for i, q in enumerate(questions, start=1):
        q = dict(q)
        q["id"] = f"{paper_id}_q{i}"
        if q.get("question", "").strip():
            renumbered.append(q)
    questions = renumbered
    if not questions:
        return None

    return {
        "metadata": {
            "name": f"{meta['title']} · {year}",
            "exam": "UPSC CSE",
            "totalQuestions": len(questions),
            "difficulty": meta["difficulty"],
            "defaultDuration": meta["default_duration"],
            "year": year,
            "stage": "Prelims" if stage == "PRELIMS" else "Mains",
            "paper": paper_code,
            "section": meta["section"],
            "sourceId": paper_id,
            "practiceMode": meta["mode"],
            "contentVersion": CONTENT_VERSION,
        },
        "questions": questions,
    }


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    if OUT.exists():
        for path in OUT.rglob("*.json"):
            path.unlink()
    else:
        OUT.mkdir(parents=True)

    catalog = []
    for path in sorted(SRC.rglob("paper.json")):
        bank = convert_paper(path)
        if not bank:
            print("skip", path)
            continue
        md = bank["metadata"]
        rel = Path(md["section"]) / f"{md['year']}.json"
        out_path = OUT / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        catalog.append(
            {
                "path": str(rel).replace("\\", "/"),
                "name": md["name"],
                "exam": md["exam"],
                "year": md["year"],
                "stage": md["stage"],
                "paper": md["paper"],
                "section": md["section"],
                "totalQuestions": md["totalQuestions"],
                "defaultDuration": md["defaultDuration"],
                "practiceMode": md["practiceMode"],
                "difficulty": md["difficulty"],
                "contentVersion": CONTENT_VERSION,
            }
        )

    catalog.sort(key=lambda item: (item["section"], -item["year"]))
    (OUT / "catalog.json").write_text(
        json.dumps(
            {"contentVersion": CONTENT_VERSION, "papers": catalog},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"converted {len(catalog)} papers (contentVersion={CONTENT_VERSION}) -> {OUT}")


if __name__ == "__main__":
    main()
