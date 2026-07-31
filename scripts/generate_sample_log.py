"""
Generate synthetic Tagmatic monitoring data.

Ava Industries' real ticket data cannot be committed to this repository, so the
dashboard ships with synthetic data that has the same schema as the live
pipeline output. The generator is seeded, so every team member gets identical
files and screenshots are reproducible.

Two files are produced, because the four KPIs are measured against two
different populations:

  data/classification_log.csv
      Live traffic. No ground-truth labels — in production nobody hand-labels
      every ticket. Supports the human-review flag rate and PII escape count.

  data/holdout_eval.csv
      A fixed 240-ticket labelled evaluation set, re-scored once per sprint
      against the current model version. Supports primary-label accuracy and
      per-label F1. Holding the set fixed is what makes sprint-over-sprint
      comparison meaningful; re-sampling live traffic each sprint would move
      the measurement and the model at the same time.

The synthetic data deliberately reproduces the drift scenario the Phase 1 risk
register predicted (R1), so the alerting path can be demonstrated end to end:

    Sprint 1     baseline state; all KPIs within limit
    Sprint 2     one PII escape; worst-label F1 enters the warning band
    Sprint 3     worst-label F1 remains in warning; review rate stays just below 15%
    Sprint 4     worst-label F1 breaches 5 pp; review rate enters warning
    Sprint 5     review rate breaches 20%; accuracy enters warning

French-language tickets are given systematically lower confidence and accuracy
throughout. That is not decoration: the classifier prompt, its few-shot
examples, and the spaCy censor pipeline are all English-validated, so French
tickets are the population where R1 and R2 concentrate.

Usage:  python scripts/generate_sample_log.py
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 409
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TAXONOMY_VERSION = "1.4.0"
MODEL_VERSION = "llama3.1:8b-instruct-q4_K_M"
CONFIDENCE_GATE = 0.72  # below this, the ticket is held for human review

TICKET_TYPES = [
    "bug_report",
    "feature_request",
    "question",
    "documentation",
    "access_request",
]
TYPE_MIX = [0.34, 0.22, 0.21, 0.11, 0.12]

WORKFLOWS = [
    "patient_intake",
    "charting",
    "orders_and_results",
    "scheduling",
    "billing",
    "reporting",
]
EMR_AREAS = [
    "clinical_documentation",
    "patient_portal",
    "lab_integration",
    "pharmacy",
    "admin_console",
    "interoperability",
]

# Per-sprint operating conditions:
#   flag_rate  target blended human-review flag rate on live traffic
#   base_acc   hold-out accuracy for every label except bug_report
#   bug_acc    hold-out accuracy for bug_report, the label drift attacks
SPRINTS = {
    1: (0.09, 0.912, 0.925),
    2: (0.11, 0.911, 0.910),
    3: (0.15, 0.910, 0.880),
    4: (0.18, 0.908, 0.845),
    5: (0.22, 0.906, 0.800),
}

# Weekly delivery cycles. Implementation began the day after the Phase 1
# proposal was submitted (2026-06-28), so five completed cycles fit between
# Phase 1 and the Phase 2 deadline. Sprint 1 doubles as the baseline run.
SPRINT_START = datetime(2026, 6, 22)
SPRINT_LENGTH_DAYS = 7
TICKETS_PER_SPRINT = 110
HOLDOUT_SIZE = 240
FRENCH_SHARE = 0.12
FRENCH_FLAG_MULTIPLIER = 2.4
FRENCH_ACCURACY_PENALTY = 0.07

# Blended rate = base * (en_share + fr_share * multiplier). Divide the target
# by this so the observed blended rate lands on the Phase 1 threshold rather
# than overshooting it.
BLEND = (1 - FRENCH_SHARE) + FRENCH_SHARE * FRENCH_FLAG_MULTIPLIER

# The single PII escape: Sprint 2, a French ticket. The English NER model did
# not recognise the patient name, and the regex set was written against the SIN
# pattern, which does not match an Alberta PHN.
PII_ESCAPE_SPRINT = 2


def pick(rng: random.Random, options, weights=None):
    return rng.choices(options, weights=weights, k=1)[0]


def confusable(rng: random.Random, true_type: str) -> str:
    """Return a plausible wrong label, not a uniformly random one."""
    neighbours = {
        "bug_report": ["question", "feature_request"],
        "feature_request": ["bug_report", "question"],
        "question": ["documentation", "bug_report"],
        "documentation": ["question", "feature_request"],
        "access_request": ["question", "bug_report"],
    }
    return pick(rng, neighbours[true_type])


def build_live_log(rng: random.Random) -> list[dict]:
    rows = []
    ticket_no = 1040
    escape_index = rng.randrange(0, TICKETS_PER_SPRINT)

    for sprint, (flag_rate, _base_acc, _bug_acc) in SPRINTS.items():
        start = SPRINT_START + timedelta(days=(sprint - 1) * SPRINT_LENGTH_DAYS)
        # Allocate flags by exact count rather than per-ticket coin flips, so
        # the observed rate lands on the Phase 1 threshold instead of near it.
        langs = [
            "fr" if (i == escape_index and sprint == PII_ESCAPE_SPRINT)
            or rng.random() < FRENCH_SHARE else "en"
            for i in range(TICKETS_PER_SPRINT)
        ]
        n_fr = langs.count("fr")
        n_en = TICKETS_PER_SPRINT - n_fr
        total_flags = round(TICKETS_PER_SPRINT * flag_rate)
        en_rate = total_flags / (n_en + FRENCH_FLAG_MULTIPLIER * n_fr)
        n_en_flag = round(en_rate * n_en)
        n_fr_flag = min(total_flags - n_en_flag, n_fr)

        en_idx = [i for i, l in enumerate(langs) if l == "en"]
        fr_idx = [i for i, l in enumerate(langs) if l == "fr"]
        flagged_idx = set(rng.sample(en_idx, n_en_flag)) | set(rng.sample(fr_idx, n_fr_flag))

        for i in range(TICKETS_PER_SPRINT):
            ticket_no += 1
            created = start + timedelta(
                days=rng.randrange(0, SPRINT_LENGTH_DAYS),
                hours=rng.randrange(7, 19),
                minutes=rng.randrange(0, 60),
            )

            escape = sprint == PII_ESCAPE_SPRINT and i == escape_index
            language = langs[i]
            flagged = i in flagged_idx

            if flagged:
                confidence = round(rng.uniform(0.38, CONFIDENCE_GATE - 0.005), 3)
                reason = "below_confidence_gate"
            else:
                confidence = round(rng.uniform(CONFIDENCE_GATE, 0.985), 3)
                reason = ""

            redacted = rng.choices([0, 1, 2, 3, 4], weights=[38, 30, 18, 9, 5])[0]
            if escape:
                redacted = max(redacted, 2)

            rows.append(
                {
                    "ticket_id": f"AVA-{ticket_no}",
                    "created_at": created.isoformat(timespec="seconds"),
                    "sprint": sprint,
                    "language": language,
                    "ticket_type_pred": pick(rng, TICKET_TYPES, TYPE_MIX),
                    "workflow_pred": pick(rng, WORKFLOWS),
                    "area_of_emr_pred": pick(rng, EMR_AREAS),
                    "confidence": confidence,
                    "flagged_for_review": int(flagged),
                    "review_reason": reason,
                    "pii_entities_redacted": redacted,
                    "pii_escape": int(escape),
                    "taxonomy_version": TAXONOMY_VERSION,
                    "model_version": MODEL_VERSION,
                }
            )
    return rows


def build_holdout(rng: random.Random) -> list[dict]:
    """A fixed labelled set, re-scored once per sprint."""
    fixture = []
    for n in range(HOLDOUT_SIZE):
        fixture.append(
            {
                "eval_id": f"HO-{n + 1:03d}",
                "language": "fr" if rng.random() < FRENCH_SHARE else "en",
                "ticket_type_true": pick(rng, TICKET_TYPES, TYPE_MIX),
            }
        )

    rows = []
    for sprint, (_flag, base_acc, bug_acc) in SPRINTS.items():
        scored_at = SPRINT_START + timedelta(days=sprint * SPRINT_LENGTH_DAYS - 2)

        # Decide which items are misclassified this sprint by exact count within
        # each (label, language) stratum. With 240 items, per-item coin flips
        # carry roughly +/-4pp of noise at 2 sigma, which is comparable to the
        # 5pp threshold being demonstrated.
        wrong = set()
        for label in TICKET_TYPES:
            for lang in ("en", "fr"):
                stratum = [
                    it["eval_id"] for it in fixture
                    if it["ticket_type_true"] == label and it["language"] == lang
                ]
                if not stratum:
                    continue
                acc = bug_acc if label == "bug_report" else base_acc
                if lang == "fr":
                    acc -= FRENCH_ACCURACY_PENALTY
                n_wrong = round(len(stratum) * (1 - acc))
                wrong.update(rng.sample(stratum, n_wrong))

        for item in fixture:
            true_type = item["ticket_type_true"]
            pred = confusable(rng, true_type) if item["eval_id"] in wrong else true_type

            rows.append(
                {
                    "eval_id": item["eval_id"],
                    "sprint": sprint,
                    "scored_at": scored_at.date().isoformat(),
                    "language": item["language"],
                    "ticket_type_true": true_type,
                    "ticket_type_pred": pred,
                    "taxonomy_version": TAXONOMY_VERSION,
                    "model_version": MODEL_VERSION,
                }
            )
    return rows


def write(rows: list[dict], name: str) -> None:
    path = DATA_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
                fh,
                fieldnames=list(rows[0].keys()),
                lineterminator="\n",
            )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):>5} rows to data/{name}")


def main() -> None:
    rng = random.Random(SEED)
    write(build_live_log(rng), "classification_log.csv")
    write(build_holdout(rng), "holdout_eval.csv")


if __name__ == "__main__":
    main()
