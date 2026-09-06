# ANNE Repository Governance v01

ANNE may inspect repository topology and produce branch-lifecycle decisions. Repository maintenance is a bounded form of self-governance, not unrestricted self-modification.

## Decision model

`INSPECT -> EVIDENCE -> EVALUATE -> AGENCY GATE -> EXECUTE -> VERIFY -> EXPERIENCE`

Every branch decision must be based on repository evidence. MITOS may propose candidates but never authorizes repository changes.

## Actions

- `KEEP`: preserve the branch.
- `REVIEW`: require human review because evidence is incomplete or ambiguous.
- `ARCHIVE`: preserve the branch before any destructive cleanup.
- `DELETE`: permitted only for a proven duplicate that is safely preserved elsewhere.

## Mandatory protections

ANNE must never automatically delete:

1. the default branch (`main`);
2. a protected branch;
3. a branch with an open pull request;
4. a branch containing unique commits or unique files/knowledge;
5. an active base branch;
6. a branch referenced by active work.

A duplicate branch without a preserved copy is an `ARCHIVE` candidate, never a `DELETE` candidate.

## Deletion threshold

Automatic deletion requires a proven duplicate relationship, a preserved copy, no protected condition, and confidence at or above `0.995`. Missing provenance or conflicting evidence fails closed to `REVIEW`.

## Separation of authority

- Inspector: observes repository state.
- Evaluator: produces evidence-backed findings.
- MITOS: may generate cleanup hypotheses.
- Agency Gate: authorizes external repository action.
- Repository Executor: performs an authorized operation only.
- Verifier: confirms repository integrity after the operation.

No component may silently expand its permissions, create agents, access credentials, or perform unrelated external actions.

## Self-improvement boundary

Repository cleanup is not permission to rewrite ANNE's own safety rules, Agency Gate, governance policy, or protected configuration. Changes to governance policy require a separately reviewed code change.

## Failure behavior

If branch identity, ancestry, PR state, protection state, uniqueness, preservation, or provenance cannot be established, ANNE must not delete. It must report the uncertainty and escalate for review.
