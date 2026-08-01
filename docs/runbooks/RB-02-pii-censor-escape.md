# Incident Runbook

| RUNBOOK ID | FAILURE MODE | RISK REGISTER REF (PHASE 1) |
|---|---|---|
| **RB-02** | PII false negative — identifiable information passes the censor and reaches the LLM, vector store, or a GitHub Issue | **R2** (Medium likelihood / High impact) · related: **R6** bilingual gap |

| SEVERITY | OWNER | LAST REVIEWED |
|---|---|---|
| **Sev 1 (P1)** | William Makino (security) · Single external contact: Barbara Alfaro (lead) | 2026-07-31 |

> **Not a worse RB-01.** Drift is recoverable — roll back and the system is well
> again. A censor escape is not: rollback restores a safe pipeline, it does not
> reverse the disclosure. Every step below is written for containment and
> evidence, not repair.

---

## SYMPTOM

Any one of the following:

- **PII censor escapes** on the dashboard reads **1 or more**. This KPI is a
  count, not a rate — there is no warn band and no Sev 3 state.
- A GitHub Issue body visibly contains a name, email, phone, PHN, postal code or
  date of birth that was never replaced with a placeholder.
- A team member reports seeing identifiable content in a ticket, log line, or
  LLM prompt.
- The client reports it. Same incident, worse starting position: the clock has
  been running and the team did not start it.

A ticket flagged for review with PII still in it is **also an escape** — the
review gate is not a censor, and the content already reached the model.

---

## DETECTION SIGNAL

| Metric | Threshold | Source |
|---|---|---|
| `pii_escapes` = `sum(pii_escape)` per sprint | **1 occurrence.** No warn band | `classification_log.csv` |

No warn band by design: PIPEDA and PIPA Alberta make a single identifiable
record reaching an external system a reportable event, so "0.9% escape rate" is
not a state the team can be inside. Traces to Phase 1 Objective 2.

**Confirm, but timebox to 30 minutes:**

```bash
pytest tests/test_censor.py -q      # does a known-good case still redact?
```

Green suite → the escape is a **new** pattern and belongs in the file as a new
case. Red suite → a censoring change regressed; `git log -- src/censor.py` names
the commit.

`pii_entities_redacted` counting up is not reassurance. It counts what was
caught and says nothing about what was missed.

---

## IMMEDIATE ACTION

**1 · Stop the bleed — before any assessment**

```bash
gh workflow disable classify-issue.yml
```

Auto-labelling goes off first. Every ticket processed while the team decides
whether this is real is processed by a censor known to have failed once. This is
the opposite of RB-01, where the pipeline stays up.

**2 · Preserve evidence — before any cleanup (≤ 30 min)**

Do **not** edit or delete the affected Issue. Redacting it destroys the record
of what was disclosed, which is exactly what the client needs to make a
notification determination. Capture ticket ID(s), destination (LLM provider,
vector store, GitHub Issue), censor version, and ticket language. Store under
access control, not in this repository.

**3 · Scope it (≤ 4 h)**

How many records, over what window, which destinations. Check whether the
language is outside `censor_validated_languages` in `config/thresholds.yaml`
(currently `en` only) — a French ticket changes the question from "one ticket"
to "every French ticket since the censor was last validated".

**Never paste escaped values into Slack, issues, or email.** Refer by ticket ID
and PII *category* only.

---

## ROLLBACK PLAN

**The known-good state is the last commit where `pytest tests/test_censor.py`
passes *with the escaping case added as a new test*.** Not the previous release,
not "before today" — without the failing case in the suite, the rollback target
is a version that would fail the same way again.

| Step | Action |
|---|---|
| 1 | Add the escaping input to `tests/test_censor.py`. It must fail against current `src/censor.py` |
| 2 | `git revert` the censoring change if one is identified; otherwise extend the patterns |
| 3 | `pytest tests/test_censor.py -q` — new case passes, nothing else regressed |
| 4 | If the ticket was in an unvalidated language, gate it: those tickets route to human review rather than auto-labelling |
| 5 | Barbara approves re-enabling: `gh workflow enable classify-issue.yml` |
| 6 | Monitor `pii_escapes` for one full sprint before treating the fix as settled |

**Rollback does not close the incident.** The pipeline is safe; the disclosure
stands. The incident closes when the client's determination is on record.

---

## STAKEHOLDERS TO NOTIFY

| # | Who | Channel | Clock | Contacted by |
|---|---|---|---|---|
| 1 | William Makino (security) | Phone | Immediate | Whoever detected it |
| 2 | Barbara Alfaro (lead) | Phone | Immediate | William |
| 3 | **Ava Industries** | Email, cc team lead | **≤ 12 h** | **Barbara only** |
| 4 | Tim Cruz (instructor) | Email | **≤ 24 h from report** | **Barbara only** |

**One contact point, always.** A privacy incident reported through three people
in ninety minutes is a second incident.

The 24-hour clock runs **continuously** — it does not pause overnight or over a
weekend. Phase 1 said both "one business day" and "within 24 hours"; for a
Friday-evening incident those differ by three days.

**The team does not decide whether the incident is notifiable.** Under PIPEDA
and PIPA Alberta the accountable organisation is Ava Industries. The team
supplies facts; the client makes the determination.

Send at 12 h even if incomplete — the client's own clock may already be running.

Full ladder and first-message contents: `docs/escalation.md` → Sev 1.

---

## POST-INCIDENT STEP

Within one sprint of containment:

1. **The failing case is permanently in the suite** — `tests/test_censor.py`,
   named for the ticket. Non-negotiable: it is what stops the same escape twice.
2. **Record the clock** — detection, client notification, instructor
   notification, elapsed against the 12 h and 24 h commitments.
3. **Register update** — new pattern class → likelihood change on R2; non-English
   ticket → evidence on **R6**; censor regression → the gap is in review, so
   revisit `.github/CODEOWNERS` routing for `src/censor.py`.
4. **Threshold review** — `pii_escapes` stays at 1 with no warn band. Confirm
   rather than reopen: it is a legal floor, not a tuning parameter, and an
   incident is exactly when someone proposes "a small allowance".
5. **Validate the language list** — adding a language without a passing test set
   converts a known gap into an unknown one.

---

**Related:** RB-01 (classification drift) · `docs/governance/RACI.md` (event 3) ·
`docs/escalation.md` (Sev 1) · `tests/test_censor.py` · `src/censor.py`