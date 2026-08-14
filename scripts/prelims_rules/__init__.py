"""Composable Prelims MCQ structural rules.

Each rule module exports check(stem, options) -> list[str] of defect codes.
validate_mcq is the thin union — thresholds live only inside rule modules.
"""
from __future__ import annotations

from typing import Any

from .assertion_reason import check as check_assertion_reason
from .code_statement_coverage import check as check_code_coverage
from .numbered_stubs import check as check_numbered_stubs
from .ocr_tokens import check as check_ocr_tokens
from .option_sanity import check as check_option_sanity
from .readability import check as check_readability

RULES = (
    check_option_sanity,
    check_ocr_tokens,
    check_code_coverage,
    check_numbered_stubs,
    check_readability,
    check_assertion_reason,
)


def option_texts(options: list | None) -> list[str]:
    out: list[str] = []
    for o in options or []:
        if isinstance(o, dict):
            out.append(str(o.get("text") or "").strip())
        else:
            out.append(str(o or "").strip())
    return out


def validate_mcq(stem: str, options: list | None = None) -> list[str]:
    """Union of all rule modules. Empty list = usable MCQ."""
    opts = option_texts(options)
    reasons: list[str] = []
    for rule in RULES:
        reasons.extend(rule(stem or "", opts))
    return sorted(set(reasons))


def check_all(stem: str, options: list | Any = None) -> list[str]:
    return validate_mcq(stem, options)
