# Incident Runbook

| RUNBOOK ID | FAILURE MODE | RISK REGISTER REF (PHASE 1) |
|---|---|---|
| **RB-01** | LLM classification drift — model output degrades against the frozen baselines | **R1** (Medium likelihood / High impact) · related: **R6** bilingual gap |

| SEVERITY | OWNER | LAST REVIEWED |
|---|---|---|
| **Sev 2** | Nehal Gadhavi (data) · Confirming: Ludwig Cardoso (monitoring) · Approver: Barbara Alfaro (lead) | 2026-07-31 |

---

## SYMPTOM

One or more KPI cards on the operations dashboard read **Breached**:
human-review flag rate, worst per-label F1 drop, or primary-label accuracy.

A card in the **Approaching** (warn) band alone does *not* open this runbook —
that is Sev 3, logged at sprint close. The warn band exists to give a sprint of
lead time, not to trigger an incident.

Secondary tell: the PM reports labels "feeling wrong" on a ticket class before
any threshold moves. Treat this as a prompt to check the dashboard, not as the
breach itself.

---

## DETECTION SIGNAL

| Metric | Warn | Breach | Source |
|---|---|---|---|
| Human-review flag rate | 15% | **> 20%** in any sprint | `classification_log.csv` |
| Worst per-label F1 drop vs. frozen baseline | 3 pp | **> 5 pp** | `holdout_eval.csv` |
| Primary-label accuracy (hold-out) | 87% | **< 85%** | `holdout_eval.csv` |

Thresholds live in `config/thresholds.yaml`; none is hard-coded. All three trace
to Phase 1 Objectives 1 and 3.

**Confirm the breach is real before acting:**

1. Check the reporting sprint and hold-out re-score timestamp on the dashboard.
2. Confirm `config/thresholds.yaml` was not edited without a PR (`git log`).
3. If the breach is accuracy or F1, re-run the hold-out scoring path — rule out
   a bad CSV write before treating it as model drift.

If the number is a data artefact, stop and file a monitoring note. Do not raise
a retune trigger on a broken measurement.

---

## IMMEDIATE ACTION

1. **Note which label(s) drove the drop.** The KPI is the worst label, not the
   average — a single collapsing class is the expected shape of this incident.
2. **Check the language split.** An elevated French flag rate points at R6
   rather than at general drift (indicative only at current volume).
3. **Compare the model and prompt version** in the dashboard masthead against
   the last known-good deploy.
4. **Raise the retune trigger within 48 hours** of the confirmed breach
   (Phase 1 Objective 1).

Auto-labelling is **not** disabled for drift. Wrong labels are correctable by a
human; the throughput cost of stopping the pipeline outweighs the error rate at
these thresholds. This is the line that separates RB-01 from RB-02.

---

## ROLLBACK PLAN

**The known-good state is the last model and prompt version whose hold-out
scores sat within the frozen baselines in `config/thresholds.yaml`.**

| Step | Action |
|---|---|
| 1 | Propose rollback to the last known-good model/prompt version, **or** a retune with hold-out results against the frozen baselines |
| 2 | Barbara approves the deploy (RACI — *Deploy a new model or prompt version*) |
| 3 | If the taxonomy changed, remove classifier-applied labels matching `AI_*` — bounded because human-applied labels carry no prefix |
| 4 | Re-baselining is a **separate** approval, not a side effect of the deploy. Ludwig reviews, Barbara approves |
| 5 | Confirm the breached KPI returns to *Within limit* on the next sprint re-score |

A metric owner who can silently move his own baseline is not a control — hence
the split approval at step 4.

---

## STAKEHOLDERS TO NOTIFY

| # | Who | Channel | When |
|---|---|---|---|
| 1 | Ludwig Cardoso (monitoring) | Team channel | On breach — confirms it is not a data artefact |
| 2 | Nehal Gadhavi (data) | Team channel | On confirmation — opens this runbook |
| 3 | Barbara Alfaro (lead) | Team channel | Before any deploy or re-baseline |
| 4 | Ava Industries | Email, via Barbara | **Only if unresolved at sprint close** |

Drift escalates on **duration**, not severity. A breach being actively retuned
is the system working as designed. A breach that survives a full sprint is a
commitment no longer being met, and the client hears it from the team rather
than from their own label quality.

Full ladder: `docs/escalation.md` → Sev 2.

---

## POST-INCIDENT STEP

Within one sprint of recovery:

1. **Record the clock** — detection to retune trigger, against the 48 h
   commitment. A miss is a finding about the runbook, not the person.
2. **Register update** — if drift concentrated in French tickets, that is
   evidence on **R6** and the question is whether it stays Proposed or is
   accepted onto the register.
3. **Threshold review** — confirm the warn band gave usable lead time. In the
   modelled scenario the flag rate crossed warn in Sprint 3 and breach in
   Sprint 5; two sprints is the design intent.
4. **Baseline check** — if re-baselined, confirm `config_version` was bumped and
   the approval is on record.

---

**Related:** RB-02 (PII censor escape) · `docs/governance/RACI.md` (event 1) ·
`docs/escalation.md` (Sev 2) · `config/thresholds.yaml` · `tests/test_metrics.py`