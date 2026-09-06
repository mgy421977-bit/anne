# Branch Inventory — 2026-09-06

## Protected / KEEP

| Branch | Reason |
|---|---|
| `main` | Canonical integration branch. Never delete. |
| `anne-mitos-architecture-20260905` | Open PR #10 head; contains unique MITOS architecture work. |
| `feat/computation-core-v01` | Open PR #7 head. |
| `feat/derivation-benchmark-01` | Open PR #6 head. |
| `anne-tinker-ollama-files-20260904` | Open PR #5 head. |
| `anne-architecture-cleanup-20260904` | Open PR #4 head. |
| `anne-github-write-tools-20260904` | Open PR #3 head. |

## Review required — not deleted

The repository contains many similarly named computation, language-learning,
MITOS, unified, and merge-work branches. They were not deleted because branch
age, unique commits, recovery value, and relationship to unpublished work cannot
be established safely from names alone. The repository policy is **UNCERTAIN →
KEEP**. A maintainer should review these branches in a separate, explicitly
approved cleanup operation.

## Duplicate architecture review

PR #10 exposed a duplicate/transition boundary between the legacy
`MythosEngine` and the new MITOS candidate API. This change keeps the legacy
engine as a compatibility implementation and adds the canonical `MitosEngine`
API rather than deleting either implementation before imports and tests are
stable.

## Cleanup result

- Branches deleted: none.
- Open PR branches protected: yes.
- Main protected: yes.
- Reason: safe cleanup requires explicit deletion authority and per-branch
  dependency verification; uncertainty is resolved by keeping the branch.
