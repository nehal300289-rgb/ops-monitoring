"""
Lightweight PII pattern checks for the regression suite.

Production uses spaCy NER; this module encodes a few high-signal patterns so
CI can fail closed without pulling the full model. Languages outside
config/thresholds.yaml → censor_validated_languages are treated as unvalidated.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
# Canadian SIN-shaped groups — deliberately coarse for regression, not validation.
SIN = re.compile(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b")

PATTERNS = {
    "email": EMAIL,
    "phone": PHONE,
    "sin": SIN,
}


def find_pii(text: str) -> list[str]:
    """Return the categories of PII patterns found in text."""
    found = []
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            found.append(name)
    return found


def redact(text: str) -> str:
    """Replace matched PII patterns with category placeholders."""
    out = text
    for name, pattern in PATTERNS.items():
        out = pattern.sub(f"[{name.upper()}]", out)
    return out


def is_validated_language(language: str, validated: list[str]) -> bool:
    """True when the censor has been validated for this language code."""
    return language in validated
