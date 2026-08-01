# RB-02 — PII censor escape

Opened on **any** occurrence of the PII escape KPI. There is no warn band and
no Sev 3 state — the first nonzero count is Sev 1.

Owner on open: William Makino (security) · Single external contact: Barbara
Alfaro (lead)

---

## 1. Contain (immediate)

1. Disable auto-labelling so no further tickets leave the controlled pipeline.
2. Preserve evidence: the offending ticket id(s), destination (LLM provider,
   vector store, GitHub Issue), and the censor version / language.
3. Do not paste escaped values into Slack, issues, or email. Refer by ticket id
   and PII *category* only.

## 2. Assess (≤ 4 h)

1. Scope: how many records, over what window, which destinations.
2. Check whether the ticket language is outside
   `censor_validated_languages` in `config/thresholds.yaml` (currently `en`
   only). French is the known concentration for R2.
3. Confirm the regression suite still covers the escaped pattern; if not, add a
   failing case in `tests/test_censor.py` before closing the incident.

## 3. Notify

Only Barbara contacts Ava Industries and the instructor. See
`docs/escalation.md` → Sev 1 for clocks (client ≤ 12 h, instructor ≤ 24 h from
**report**) and the first-message contents.

The team does not decide whether the incident is notifiable under PIPEDA /
PIPA Alberta — Ava Industries does.

## 4. Post-incident (≤ 1 sprint)

1. Ship the regression fix; green `pytest tests/test_censor.py` is the exit
   gate for re-enabling auto-labelling.
2. Update the Phase 1 risk register note for R2 with elapsed time from report.
3. Barbara closes the incident after the client acknowledgement is on record.
