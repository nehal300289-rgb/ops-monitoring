"""
Tagmatic operational metrics.

Kept separate from the Streamlit layer so the same computations can be called
from a scheduled job, a test, or a GitHub Action without importing a UI
framework. Every threshold comparison reads from config/thresholds.yaml — no
threshold is hard-coded here.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

def _find_root(start: Path) -> Path:
    """Locate the project folder by walking up until config/thresholds.yaml appears.

    Deliberately not a fixed number of parent hops: this file has to keep working
    whether it sits in src/ or at the repository root, and a hard-coded depth
    fails silently by resolving to the wrong directory.
    """
    for candidate in (start, *start.parents):
        if (candidate / "config" / "thresholds.yaml").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find config/thresholds.yaml above "
        f"{start}. Check that config/, data/ and src/ sit together in the project folder."
    )


ROOT = _find_root(Path(__file__).resolve().parent)
CONFIG_PATH = ROOT / "config" / "thresholds.yaml"
LIVE_PATH = ROOT / "data" / "classification_log.csv"
HOLDOUT_PATH = ROOT / "data" / "holdout_eval.csv"

OK, WARN, BREACH = "ok", "warn", "breach"


@dataclass(frozen=True)
class Kpi:
    """A single measured KPI with everything needed to act on it."""

    key: str
    label: str
    value: float
    display: str
    status: str
    warn_at: float | None
    breach_at: float
    threshold_text: str
    rationale: str
    source: str
    risk_ref: str
    runbook: str


@lru_cache(maxsize=1)
def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def load_live() -> pd.DataFrame:
    df = pd.read_csv(LIVE_PATH, parse_dates=["created_at"])
    df["review_reason"] = df["review_reason"].fillna("")
    return df


@lru_cache(maxsize=1)
def load_holdout() -> pd.DataFrame:
    return pd.read_csv(HOLDOUT_PATH, parse_dates=["scored_at"])


def sprints() -> list[int]:
    return sorted(load_live()["sprint"].unique().tolist())


def classify(
    value: float,
    warn_at: float | None,
    breach_at: float,
    higher_is_better: bool,
) -> str:
    """Return ok / warn / breach for a value against its configured bands.

    Thresholds come from config/thresholds.yaml — never hard-coded at the call
    site. Phase 1 defined breach points only; Phase 2 added warn bands so the
    on-call person gets a Sev 3 signal before a Phase 1 commitment is lost.

    ``warn_at`` may be ``None`` when a KPI has no warning band. That is the
    intentional design for PII escapes: zero is within limit, and any
    occurrence is immediately a breach (Sev 1), with no intermediate state.
    """
    if higher_is_better:
        if value < breach_at:
            return BREACH
        if warn_at is not None and value < warn_at:
            return WARN
        return OK
    if value >= breach_at:
        return BREACH
    if warn_at is not None and value > warn_at:
        return WARN
    return OK


def f1_per_label(frame: pd.DataFrame) -> dict[str, float]:
    """Per-label F1 from a frame with ticket_type_true / ticket_type_pred.

    Computed directly rather than via scikit-learn: it is a handful of lines,
    it keeps the deployed dependency set to streamlit + pandas + pyyaml, and it
    leaves the definition visible to a reviewer checking the drift maths.
    """
    scores = {}
    for label in sorted(frame["ticket_type_true"].unique()):
        tp = int(((frame.ticket_type_pred == label) & (frame.ticket_type_true == label)).sum())
        fp = int(((frame.ticket_type_pred == label) & (frame.ticket_type_true != label)).sum())
        fn = int(((frame.ticket_type_pred != label) & (frame.ticket_type_true == label)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores[label] = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return scores


def f1_table(sprint: int) -> pd.DataFrame:
    """Per-label F1 for one sprint, against the frozen Phase 1 baselines."""
    cfg = load_config()
    baselines = cfg["baselines"]
    breach_at = cfg["kpis"]["per_label_f1_delta"]["breach_at"]
    warn_at = cfg["kpis"]["per_label_f1_delta"]["warn_at"]

    current = f1_per_label(load_holdout().query("sprint == @sprint"))
    rows = []
    for label, score in sorted(current.items()):
        baseline = baselines.get(label)
        delta = (baseline - score) if baseline is not None else float("nan")
        rows.append(
            {
                "Label": label,
                "Baseline F1": baseline,
                "Current F1": round(score, 4),
                "Drop (pp)": round(delta * 100, 1),
                "Status": classify(delta, warn_at, breach_at, higher_is_better=False),
            }
        )
    return pd.DataFrame(rows)


def flag_rate_by_sprint() -> pd.DataFrame:
    live = load_live()
    out = live.groupby("sprint")["flagged_for_review"].mean().reset_index()
    out.columns = ["sprint", "flag_rate"]
    return out


def flag_rate_by_language(sprint: int) -> pd.DataFrame:
    live = load_live().query("sprint == @sprint")
    out = (
        live.groupby("language")
        .agg(tickets=("ticket_id", "size"), flag_rate=("flagged_for_review", "mean"))
        .reset_index()
    )
    out["language"] = out["language"].map({"en": "English", "fr": "French"}).fillna(out["language"])
    return out.sort_values("flag_rate", ascending=False)


def accuracy_by_sprint() -> pd.DataFrame:
    ho = load_holdout()
    ho = ho.assign(correct=(ho.ticket_type_pred == ho.ticket_type_true))
    out = ho.groupby("sprint")["correct"].mean().reset_index()
    out.columns = ["sprint", "accuracy"]
    return out


def worst_f1_drop(sprint: int) -> tuple[str, float]:
    table = f1_table(sprint)
    row = table.loc[table["Drop (pp)"].idxmax()]
    return row["Label"], float(row["Drop (pp)"]) / 100


def compute_kpis(sprint: int) -> list[Kpi]:
    """The four KPIs the Phase 1 operations plan committed the team to."""
    cfg = load_config()
    k = cfg["kpis"]
    live = load_live().query("sprint == @sprint")
    holdout = load_holdout().query("sprint == @sprint")

    flag_rate = float(live["flagged_for_review"].mean())
    escapes = int(live["pii_escape"].sum())
    accuracy = float((holdout.ticket_type_pred == holdout.ticket_type_true).mean())
    worst_label, worst_drop = worst_f1_drop(sprint)

    def build(key: str, value: float, display: str, threshold_text: str, higher: bool) -> Kpi:
        spec = k[key]
        return Kpi(
            key=key,
            label=spec["label"],
            value=value,
            display=display,
            status=classify(value, spec["warn_at"], spec["breach_at"], higher),
            warn_at=spec["warn_at"],
            breach_at=spec["breach_at"],
            threshold_text=threshold_text,
            rationale=" ".join(spec["rationale"].split()),
            source=spec["source"],
            risk_ref=spec["risk_ref"],
            runbook=spec["runbook"],
        )

    return [
        build(
            "review_flag_rate",
            flag_rate,
            f"{flag_rate:.1%}",
            "Alert above 20% in any sprint",
            higher=False,
        ),
        build(
            "per_label_f1_delta",
            worst_drop,
            f"{worst_drop * 100:.1f} pp",
            f"Alert above 5 pp drop · worst: {worst_label}",
            higher=False,
        ),
        build(
            "primary_label_accuracy",
            accuracy,
            f"{accuracy:.1%}",
            "Alert below 85% on the hold-out set",
            higher=True,
        ),
        build(
            "pii_escapes",
            escapes,
            str(escapes),
            "Any occurrence is a P1 incident",
            higher=False,
        ),
    ]