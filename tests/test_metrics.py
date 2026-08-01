"""Unit tests for KPI warn / breach band classification."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from metrics import BREACH, OK, WARN, classify  # noqa: E402


def test_lower_is_better_ok_warn_breach():
    # review-flag rate: warn 15%, breach 20%
    assert classify(0.10, 0.15, 0.20, higher_is_better=False) == OK
    assert classify(0.16, 0.15, 0.20, higher_is_better=False) == WARN
    assert classify(0.20, 0.15, 0.20, higher_is_better=False) == BREACH
    assert classify(0.25, 0.15, 0.20, higher_is_better=False) == BREACH


def test_higher_is_better_ok_warn_breach():
    # primary-label accuracy: warn 87%, breach below 85%
    assert classify(0.90, 0.87, 0.85, higher_is_better=True) == OK
    assert classify(0.86, 0.87, 0.85, higher_is_better=True) == WARN
    assert classify(0.84, 0.87, 0.85, higher_is_better=True) == BREACH


def test_pii_escape_has_no_warn_band():
    # Any occurrence is a breach; zero is within limit (no Sev 3 state).
    assert classify(0, None, 1, higher_is_better=False) == OK
    assert classify(1, None, 1, higher_is_better=False) == BREACH
    assert classify(3, None, 1, higher_is_better=False) == BREACH
