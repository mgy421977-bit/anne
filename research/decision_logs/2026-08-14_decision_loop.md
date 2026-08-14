# Decision Log — 2026-08-14

## Subject

Add `DecisionLoop` as a thin facade over existing FailFast + `AnnePipeline`.

## Decision

1. Implement `src/anne/core/decision_loop.py` with `DecisionResult`.
2. **Do not** name it ConsciousnessLoop or claim immutable/unhackable core.
3. **Do not** reimplement stages; delegate to `AnnePipeline.run_with_fail_fast`.
4. Document as preferred application entry path; Stage ABC remains for ablations.

## Rationale

Applications need one mandatory gate path. A facade preserves Core Rules design intent without parallel ethics logic or overclaim.

## Status

| Item | Label |
|------|--------|
| DecisionLoop facade | **Implemented** |
| Full migration of all examples to DecisionLoop | **Future** |
| Consciousness / absolute core packaging | **Rejected** |
