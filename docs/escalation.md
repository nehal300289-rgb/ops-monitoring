# Escalation Paths

Who is contacted, in what order, through which channel — and who is allowed to
make the call.

Owner: Barbara Alfaro (team lead) · Last reviewed: 2026-07-31

---

## Severity definitions

| Sev | Meaning | Clock | Escalates to client? |
|---|---|---|---|
| **Sev 1** | Personal information has left the controlled pipeline. Irreversible. | Contain immediately · client ≤ 12 h · instructor ≤ 24 h | Yes, always |
| **Sev 2** | Classification is degraded past a Phase 1 commitment. Recoverable. | Retune trigger ≤ 48 h | Only if unresolved at sprint close |
| **Sev 3** | A metric is inside a warning band. No commitment breached yet. | Review at sprint close | No |

The distinction that matters: **Sev 1 is not a worse Sev 2.** A drift incident
is recovered by rolling back to a known-good configuration. A censor escape
cannot be rolled back — the pipeline can be restored, the disclosure cannot be
reversed. That is why Sev 1 escalates externally on a fixed clock and Sev 2
does not.

---

## Contacts

| Role | Person | Channel | When |
|---|---|---|---|
| Team lead | Barbara Alfaro | Team channel · phone for Sev 1 | Any Sev 1, or any Sev 2 unresolved at 48 h |
| Monitoring owner | Ludwig Cardoso | Team channel | KPI breach, threshold or baseline questions |
| Data owner | Nehal Gadhavi | Team channel | Drift, retune, taxonomy |
| Security owner | William Makino | Team channel · phone for Sev 1 | Any PII escape |
| Client — Ava Industries | *(client contact, TBC)* | Email, cc team lead | Sev 1 always · Sev 2 at sprint close if unresolved |
| Instructor | Tim Cruz | Email | Sev 1 within 24 h of report |

> **To complete before submission:** the named client contact and the agreed
> channel. Escalating to "Ava Industries" without a person and a method is not
> a path, it is an intention.

---

## Sev 1 — PII censor escape

Only the team lead contacts the client. Not the person who found the escape,
not the security owner, not whoever is closest to the keyboard. A privacy
incident reported through three different people in ninety minutes is a second
incident.

```
Escape detected (any team member)
        │
        ▼
William Makino ──────── contains, preserves evidence, scopes  (≤ 4 h)
        │
        ▼
Barbara Alfaro ──────── single point of contact from here on
        │
        ├──────────────► Ava Industries        (≤ 12 h, email + cc team)
        │                        │
        │                        ▼
        │                 Client determines breach-notification
        │                 obligation under PIPEDA / PIPA Alberta
        │
        └──────────────► Tim Cruz, instructor  (≤ 24 h from report)
```

What goes to the client, in the first message:

- What escaped — category of personal information, not the values themselves
- Where it reached — LLM provider, GitHub Issue, logs
- How many records, and over what window
- What has been contained already
- What the team has **not** yet determined

The last line matters. An assessment sent late because it was being polished is
worse than a partial assessment sent on time — the client's own notification
clock may already be running and they cannot start it on information they do
not have.

**The team does not decide whether the incident is notifiable.** Under PIPEDA
and PIPA Alberta that determination belongs to Ava Industries as the accountable
organisation. The team supplies the facts; the client makes the call.

---

## Sev 2 — classification drift

Stays internal while it is being worked.

```
KPI breach on dashboard
        │
        ▼
Ludwig Cardoso ──── confirms breach is real, not a data artefact
        │
        ▼
Nehal Gadhavi ───── opens RB-01, retune trigger raised    (≤ 48 h)
        │
        ▼
Barbara Alfaro ──── approves the retune and any re-baselining
        │
        ▼
   Resolved at sprint close? ──── yes ──► note in sprint summary, no escalation
        │
        no
        │
        ▼
Ava Industries ──── informed, with the current accuracy figure and the plan
```

Drift is escalated on **duration**, not on severity. A breach that is being
actively retuned is the system working as designed. A breach that has survived
a full sprint is a commitment the team is no longer meeting, and the client is
entitled to know before they hear it from their own label quality.

---

## Sev 3 — warning band

No escalation. Logged at sprint close by the monitoring owner and reviewed in
the sprint summary.

The warn bands exist so that this level has somewhere to live. Phase 1 defined
breach points only, which meant every signal arrived as a Sev 2. Sprint 3 of
the current scenario is the case in point: the flag rate entered the warning
band two sprints before it breached, and under the Phase 1 design nobody would
have seen it.

---

## Out-of-hours

A Sev 1 detected outside working hours is contained immediately by whoever
detects it — auto-labelling is disabled first and the assessment happens after.
The team lead is contacted by phone, not by channel message.

The 24-hour instructor clock and the 12-hour client clock run continuously.
They do not pause overnight or over a weekend. This was the reason for
collapsing Phase 1's "one business day" into a fixed 24 hours: for an incident
reported on a Friday evening, the two phrasings differ by three days.
