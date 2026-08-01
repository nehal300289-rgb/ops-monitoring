"""PII censor regression suite — patterns that must never escape containment."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from censor import contains_pii, redact_pii  # noqa: E402


def test_email_detected_and_redacted():
    raw = "Contact me at jane.doe@ava-industries.example about the outage."
    assert contains_pii(raw)
    redacted = redact_pii(raw)
    assert "@" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert not contains_pii(redacted)


def test_phone_detected_and_redacted():
    raw = "Callback number is (403) 555-0199."
    assert contains_pii(raw)
    redacted = redact_pii(raw)
    assert "555" not in redacted
    assert "[REDACTED_PHONE]" in redacted


def test_sin_detected_and_redacted():
    raw = "SIN on file: 123-456-789"
    assert contains_pii(raw)
    redacted = redact_pii(raw)
    assert "123" not in redacted
    assert "[REDACTED_SIN]" in redacted


def test_clean_ticket_passes():
    raw = "The login page returns 503 after deploy. Please investigate."
    assert not contains_pii(raw)
    assert redact_pii(raw) == raw
