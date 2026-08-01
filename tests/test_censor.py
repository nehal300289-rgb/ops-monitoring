"""PII censor regression suite.

Locks the Phase 1 Objective 2 contract: any escape is a P1, the censor is only
validated for English, and the synthetic scenario models a French-ticket escape.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import censor  # noqa: E402


class TestCensorPatterns(unittest.TestCase):
    def test_redacts_email_phone_and_sin(self):
        raw = "Contact jane@ava.test or +1 (403) 555-0199. SIN 123-456-789."
        redacted = censor.redact(raw)
        self.assertIn("[EMAIL]", redacted)
        self.assertIn("[PHONE]", redacted)
        self.assertIn("[SIN]", redacted)
        self.assertEqual(censor.find_pii(redacted), [])

    def test_clean_text_has_no_pii(self):
        self.assertEqual(censor.find_pii("Printer offline in building B."), [])


class TestCensorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "config" / "thresholds.yaml").open(encoding="utf-8") as fh:
            cls.cfg = yaml.safe_load(fh)
        cls.live = pd.read_csv(ROOT / "data" / "classification_log.csv")

    def test_any_escape_is_a_breach(self):
        spec = self.cfg["kpis"]["pii_escapes"]
        self.assertEqual(spec["breach_at"], 1)
        self.assertIsNone(spec["warn_at"])

    def test_only_english_is_validated(self):
        validated = self.cfg["censor_validated_languages"]
        self.assertEqual(validated, ["en"])
        self.assertTrue(censor.is_validated_language("en", validated))
        self.assertFalse(censor.is_validated_language("fr", validated))

    def test_synthetic_escape_is_french_sprint_two(self):
        escapes = self.live.query("pii_escape == 1")
        self.assertEqual(len(escapes), 1)
        row = escapes.iloc[0]
        self.assertEqual(int(row["sprint"]), 2)
        self.assertEqual(row["language"], "fr")


if __name__ == "__main__":
    unittest.main()
