"""
Lightweight PII pattern checks used by the regression suite.

The production censor is spaCy-based and English-validated (see
config/thresholds.yaml → censor_validated_languages). This module encodes the
minimum patterns the suite asserts must never reach the LLM provider, the
vector store, or a GitHub Issue — the same surfaces Phase 1 Objective 2 named
as escape destinations.
"""

from __future__ import annotations

import re

# Conservative patterns: catch the common English forms the synthetic data and
# demo tickets use. Not a substitute for the spaCy NER pipeline in production.
_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
)
_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)",
)
_SIN = re.compile(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b")

_PATTERNS: tuple[re.Pattern[str], ...] = (_EMAIL, _PHONE, _SIN)


def contains_pii(text: str) -> bool:
    """Return True if any supported PII pattern appears in text."""
    if not text:
        return False
    return any(p.search(text) for p in _PATTERNS)


def redact_pii(text: str) -> str:
    """Replace supported PII patterns with typed placeholders."""
    if not text:
        return text
    out = _EMAIL.sub("[REDACTED_EMAIL]", text)
    out = _PHONE.sub("[REDACTED_PHONE]", out)
    out = _SIN.sub("[REDACTED_SIN]", out)
    return out
