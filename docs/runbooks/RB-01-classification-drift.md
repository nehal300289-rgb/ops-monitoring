# RB-01 — Classification drift

Opened when any of the three R1 KPIs is **Breached** on the operations
dashboard: human-review flag rate, worst per-label F1 drop, or primary-label
accuracy. A metric in the **Approaching** (warn) band alone does not open this
runbook — that is Sev 3 and is logged at sprint close.

Owner on open: Nehal Gadhavi (data) · Confirming: Ludwig Cardoso (monitoring) ·
Approver: Barbara Alfaro (lead)

---

## 1. Confirm the breach is real

1. Check the reporting sprint and hold-out re-score timestamp on the dashboard.
2. Confirm `config/thresholds.yaml` was not edited without a PR.
3. Re-run the hold-out scoring path if the breach is accuracy or F1 — rule out
   a bad CSV write before treating it as model drift.

If the number is a data artefact, stop here and file a monitoring note. Do not
raise a retune trigger on a broken measurement.

## 2. Contain and diagnose

1. Note which label(s) drove the F1 drop and whether French-language flag rate
   is elevated (indicative, not significant at current volume).
2. Compare current prompt / model version in the masthead against the last
   known-good deploy.
3. Raise the retune trigger within **48 hours** of confirmed breach
   (Phase 1 Objective 1).

## 3. Recover

1. Propose rollback to the last known-good model or prompt, **or** a retune
   with hold-out results against the frozen baselines.
2. Barbara approves deploy and any re-baselining (see RACI — Deploy a new
   model or prompt version). Re-baselining is a separate approval, not a side
   effect of the deploy.
3. After recovery, confirm the breached KPI returns to Within limit on the next
   sprint re-score.

Escalation if unresolved at sprint close: `docs/escalation.md` → Sev 2.
