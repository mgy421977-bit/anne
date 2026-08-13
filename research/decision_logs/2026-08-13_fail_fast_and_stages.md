# Decision Log — 2026-08-13

## Subject

Adopt **fail-fast pre-gate** and **swappable Stage protocol** as the next architecture increment.

## Decision

1. Implement deterministic `FailFastGate` before ANLA (optional, default on).
2. Introduce `Stage` / `StageContext` / `StagePipeline` under `src/anne/core/stages/`.
3. Wire `AnnePipeline.run_with_fail_fast(...)` convenience path; keep existing stage methods stable.
4. **Do not** claim comprehensive safety moderation or plugin marketplace maturity.
5. Defer meta-ANLA, vector hybrid memory, and HITL UI.

## Rationale

From the external suggestion list, these two items maximize research leverage with minimal scope risk:

- Fail-fast reserves ANLA for grey-zone semantic work; obvious rejects are cheap and inspectable.
- Stage ABC makes “ANLA off / custom validator” a configuration concern — matching ablation philosophy.

## Non-goals

- Domain-specific medical/legal production scorers as “ready” modules
- MatrAIx integration
- Parallel LLM perception pack (profile first)

## Status labels

| Item | Label |
|------|--------|
| FailFastGate + tests | **Implemented** |
| Stage protocol | **Implemented** (scaffold) |
| Full migration of DUY…YAP into Stage classes | **Future** |
| Meta-validation of ANLA decisions | **Future Research** |

## Verdict

Ship the thin, honest increment; measure next; expand later.
