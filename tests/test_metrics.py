"""Unit tests for KPI band classification and sprint KPI computation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import metrics as m  # noqa: E402


class TestClassify(unittest.TestCase):
    def test_lower_is_better_bands(self):
        self.assertEqual(m.classify(0.10, 0.15, 0.20, higher_is_better=False), m.OK)
        self.assertEqual(m.classify(0.16, 0.15, 0.20, higher_is_better=False), m.WARN)
        self.assertEqual(m.classify(0.20, 0.15, 0.20, higher_is_better=False), m.BREACH)

    def test_higher_is_better_bands(self):
        self.assertEqual(m.classify(0.90, 0.87, 0.85, higher_is_better=True), m.OK)
        self.assertEqual(m.classify(0.86, 0.87, 0.85, higher_is_better=True), m.WARN)
        self.assertEqual(m.classify(0.84, 0.87, 0.85, higher_is_better=True), m.BREACH)

    def test_no_warning_band_for_pii(self):
        # Phase 1 Objective 2: zero is within limit; one occurrence is immediate breach.
        self.assertEqual(m.classify(0, None, 1, higher_is_better=False), m.OK)
        self.assertEqual(m.classify(1, None, 1, higher_is_better=False), m.BREACH)


class TestComputeKpis(unittest.TestCase):
    def test_sprint_one_is_clear(self):
        statuses = {k.key: k.status for k in m.compute_kpis(1)}
        self.assertEqual(statuses["pii_escapes"], m.OK)
        self.assertTrue(all(s in {m.OK, m.WARN} for s in statuses.values()))

    def test_sprint_two_has_pii_breach(self):
        by_key = {k.key: k for k in m.compute_kpis(2)}
        self.assertEqual(by_key["pii_escapes"].status, m.BREACH)
        self.assertEqual(by_key["pii_escapes"].value, 1)


if __name__ == "__main__":
    unittest.main()
