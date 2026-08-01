# Governance RACI

Who decides, who does the work, and who is told — for the three governance
events that change how the Tagmatic classifier behaves in production.

Owner: Barbara Alfaro (team lead) · Last reviewed: 2026-07-31

---

## Why these three events

The Phase 2 brief offers "pushing a new model version, a bias complaint, a
privacy incident" as examples. Two of those are used here; the third is not.

A bias complaint would have read well as a governance event, but Phase 1 never
registered bias as a risk, so a RACI row for it would control nothing. A
taxonomy change is registered — it is **R3, Unauthorized taxonomy
modification**, rated High likelihood — and it currently has no named approver
anywhere. That gap is worth more than a tidy example.

Each row below maps to a Phase 1 risk and to the NIST AI RMF function it
operationalises.

---

## The matrix

| Governance event | Accountable | Responsible | Consulted | Informed | Phase 1 risk | AI RMF |
|---|---|---|---|---|---|---|
| Deploy a new model or prompt version | Barbara | Nehal | Ludwig, William | Client, instructor | R1 | Manage |
| Change the label taxonomy (YAML) | Barbara | Nehal | Ludwig, William | Team, client | R3 | Govern |
| PII censor escape (privacy incident) | Barbara | William | Ava Industries, Nehal | Instructor, team | R2 | Manage |

**R** — completes or drives the work
**A** — owns the final outcome and the decision
**C** — provides input before the decision is made
**I** — kept updated on progress and outcome

---

## Two lines this matrix draws deliberately

**The lead is Accountable on all three events and Responsible on none.**
Accountability that also carries the work is not accountability — the person
doing the retune cannot be the person who signs off that the retune was
warranted. This is the same separation that keeps the monitoring owner from
re-baselining his own metrics without review (see `config/thresholds.yaml`,
change control block).

**On a privacy incident the client is Consulted, not Accountable.**
This is not the team declining responsibility. Under PIPEDA and PIPA Alberta
the accountable organisation for the personal information is Ava Industries,
and the breach-notification determination is legally theirs to make. The matrix
records that external accountability rather than overriding it. The team
contains, evidences, and reports; the client decides what is notifiable and to
whom. `docs/runbooks/RB-02-pii-censor-escape.md` routes the same way.

---

## Event detail

### 1 · Deploy a new model or prompt version

Triggered by an approved retune following RB-01, or by a planned model upgrade.

| Step | Who |
|---|---|
| Propose the change, with hold-out results against the current baseline | Nehal (R) |
| Review threshold and baseline impact | Ludwig (C) |
| Review censor compatibility with the new model | William (C) |
| Approve or reject the deployment | Barbara (A) |
| Notify client and instructor after deployment | Barbara (A) |

A model change invalidates the frozen per-label baselines in
`config/thresholds.yaml`. Re-baselining is a separate approval, not a side
effect of the deployment — otherwise a bad deploy silently redefines what
"normal" means.

### 2 · Change the label taxonomy (YAML)

Triggered at sprint close, or on any recurrence of the unknown-label pattern in
logs.

| Step | Who |
|---|---|
| Open a PR against the taxonomy files | Nehal (R) |
| Review classification impact on the hold-out set | Ludwig (C) |
| Review whether new labels expand the PII surface | William (C) |
| Approve and merge | Barbara (A) |
| Notify team and client of the new vocabulary | Barbara (A) |

This row is the control for R3. Phase 1 registered unauthorized taxonomy
modification as High likelihood precisely because YAML files are easy to edit
and the consequences are invisible until classification degrades at scale.
Requiring a PR with a named approver is the whole mitigation.

### 3 · PII censor escape (privacy incident)

Triggered by any occurrence of the PII escape KPI — a single event, not a rate.
The regression suite in `tests/test_censor.py` guards the pattern checks that
back this KPI; a failing censor test is treated as a release blocker, not a
nice-to-have.

| Step | Who | Clock |
|---|---|---|
| Contain: disable auto-labelling, preserve evidence | William (R) | Immediate |
| Assess scope: what escaped, where it reached | William (R), Nehal (C) | ≤ 4 h |
| Notify Ava Industries with the assessment | Barbara (A) | ≤ 12 h |
| Client determines breach-notification obligation | Ava Industries (C) | Client's clock |
| Report to instructor | Barbara (A) | ≤ 24 h |
| Post-incident: regression test, register update | William (R), Barbara (A) | ≤ 1 sprint |

The 24-hour commitment runs from the moment the escape is **reported**, not
from when it occurred. Phase 1 Objective 2 stated both "one business day" and
"within 24 hours"; this matrix and RB-02 use 24 hours from report, and the
post-incident step records elapsed time against it.

Escalation contacts and channels: `docs/escalation.md`

---

## Traceability

| RACI event | Phase 1 risk | Runbook | KPI |
|---|---|---|---|
| Deploy new model / prompt | R1 — LLM classification drift | RB-01 | Review-flag rate · per-label F1 · accuracy |
| Change label taxonomy | R3 — Unauthorized taxonomy modification | — | Accuracy (hold-out) |
| PII censor escape | R2 — PII false negative | RB-02 | PII censor escapes |

R4 (key-person dependency) and R5 (demo-day scope creep) are not governance
events — they are managed through the contribution split and the Phase 3 scope
line, not through an approval path.
