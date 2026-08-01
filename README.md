# Tagmatic — Operations Monitoring

Operational dashboard for the Tagmatic ticket classifier. Answers one question
for whoever is on call: **is any commitment made in the Phase 1 operations plan
currently breached, and if so, which runbook do I open?**

Built for ARTI 409 Final Project, Phase 2 · Team: The Outliers.

---

## Run it

```bash
pip install -r requirements.txt
python scripts/generate_sample_log.py     # writes data/*.csv
streamlit run src/dashboard.py            # opens on http://localhost:8501
```

The sample generator is seeded, so everyone on the team sees identical numbers
and screenshots are reproducible.

---

## The four KPIs

Each KPI enforces an operational commitment established in Phase 1. The breach
thresholds trace directly to §2 of the Phase 1 proposal. Phase 2 adds warning
bands for the three performance KPIs so the team receives an early signal
before a Phase 1 commitment is breached. The PII escape KPI intentionally has
no warning band because any occurrence triggers incident handling.

| KPI | Alert threshold | Where the number comes from | Risk | Runbook |
|---|---|---|---|---|
| Human-review flag rate | Warn 15%, breach **20%** in any sprint | Phase 1 Objective 1 set 20% as a retuning trigger. The confidence gate is the safety mechanism, so a rising flag rate is the earliest visible sign the model no longer fits the ticket vocabulary. The 15% warn band was added in Phase 2 to buy a sprint of lead time instead of discovering the breach at sprint close. | R1 | RB-01 |
| Worst per-label F1 drop vs baseline | Warn 3pp, breach **5pp** | Phase 1 Objective 1 set a 5 percentage-point drop on any single label as a retuning trigger. Measured per label rather than in aggregate, because a rare but high-impact ticket type can collapse while overall accuracy holds. | R1 | RB-01 |
| Primary-label accuracy (hold-out) | Warn 87%, breach below **85%** | Phase 1 Objective 3 committed to holding primary-label accuracy above 85% for the project lifecycle. Measured on the fixed hold-out set, not live traffic, so it is comparable across model versions. | R1 | RB-01 |
| PII censor escapes | **Any occurrence** is a P1 | Phase 1 Objective 2 classified any PII false negative as a P1 incident requiring triage, containment and a report to the instructor within 24 hours. There is no acceptable non-zero rate, so the threshold is one occurrence, not a rate. | R2 | RB-02 |

Risk IDs refer to the Phase 1 risk register: **R1** LLM classification drift,
**R2** PII false negative.

---

## Layout

```
ops-monitoring/
├── .github/
│   └── CODEOWNERS             review + approval routing per artefact
├── .streamlit/
│   └── config.toml            Streamlit theme configuration
├── config/
│   └── thresholds.yaml        alert bands + frozen F1 baselines
├── data/
│   ├── classification_log.csv synthetic simulated classifier traffic
│   └── holdout_eval.csv       fixed synthetic labelled set
├── docs/
│   ├── governance/
│   │   └── RACI.md            who decides, does, is consulted, is told
│   ├── runbooks/
│   │   ├── RB-01-...md        classification drift
│   │   └── RB-02-...md        PII censor escape
│   └── escalation.md          severity ladder + client contact paths
├── scripts/
│   └── generate_sample_log.py seeded synthetic data generator
├── src/
│   ├── censor.py              lightweight PII pattern checks for regression
│   ├── metrics.py             KPI computation, no UI imports
│   └── dashboard.py           Streamlit layer
├── tests/
│   ├── test_censor.py         PII censor regression suite
│   └── test_metrics.py        warn / breach band classification
├── .gitignore
├── requirements.txt
└── README.md
```

Two design decisions worth calling out to a reviewer:

**Thresholds live in config, not code.** They are governance artefacts, so
changes go through a PR and leave an audit trail — the same argument that puts
the label taxonomy in YAML. Reviewer is the monitoring owner, approver is the
team lead. Nobody edits thresholds on `main`.

**Metrics are separate from the UI.** `src/metrics.py` imports pandas and yaml
but not Streamlit, so the same computations can be called from a scheduled job
or a GitHub Action later without dragging in a web framework.

---

## When a KPI breaches

The dashboard names the runbook; the runbook names the procedure; the RACI
names who approves it. Every path below resolves — a runbook that cites a file
which does not exist is a document, not a procedure.

| Artefact | What it answers |
|---|---|
| [`docs/runbooks/`](docs/runbooks/) | What do I do right now, and how do I roll back? |
| [`docs/governance/RACI.md`](docs/governance/RACI.md) | Who approves the fix, and who has to be told? |
| [`docs/escalation.md`](docs/escalation.md) | Who do I contact, in what order, on what clock? |
| [`.github/CODEOWNERS`](.github/CODEOWNERS) | Who has to review a change to any of the above? |

Governance events map to the Phase 1 risk register rather than to generic
examples: a model or prompt deployment controls **R1**, a taxonomy change
controls **R3**, and a censor escape controls **R2**. Two Phase 1 risks — key-person
dependency (R4) and demo-day scope creep (R5) — are managed through the
contribution split and the Phase 3 scope line, not through an approval path.

---

## Two data sources, not one

The four KPIs are measured against different populations, and conflating them
would make the drift numbers meaningless.

`data/classification_log.csv` is **synthetic simulated classifier traffic**. It contains no ground-truth labels, mirroring the intended production
monitoring structure where every incoming ticket is not independently
hand-labelled. It supports the review-flag rate and PII escape count.

`data/holdout_eval.csv` is a **fixed 240-ticket labelled set**, re-scored once
per sprint against the current model version. It supports accuracy and
per-label F1. Holding the set fixed is what makes sprint-over-sprint comparison
mean anything — re-sampling live traffic each sprint would move the measurement
and the model at the same time, and you could no longer tell which one drifted.

---

## About the sample data

Ava Industries' ticket content is not committed to this repository. The
generator produces synthetic records with the same schema as the live pipeline,
seeded to reproduce the drift scenario the Phase 1 register predicted under R1,
so the alerting path can be demonstrated end to end:

- Sprint 1 — synthetic baseline established; all metrics within limit
- Sprint 2 — one synthetic PII escape; worst-label F1 enters the warning band
- Sprint 3 — worst-label F1 remains in warning; review-flag rate remains just below 15%
- Sprint 4 — worst-label F1 breaches 5pp; review-flag rate enters the warning band
- Sprint 5 — review-flag rate breaches 20%; `bug_report` F1 remains breached at a 7.6pp drop; accuracy enters the warning band

French-language tickets are given systematically lower confidence and accuracy
throughout. That is not decoration. The classifier prompt, its few-shot
examples, and the spaCy censor pipeline are all English-validated, so French
tickets are the population where R1 and R2 concentrate — a French ticket is
both more likely to be misclassified and more likely to carry PII past the
censor. The single modelled escape is a French ticket for exactly this reason.
Per-sprint French volume is small, so the dashboard labels that panel
indicative rather than significant.

**Before the live cut-over**, replace `scripts/generate_sample_log.py` with a
reader over the real classifier output and re-establish baselines from a real
Sprint 1 run.
