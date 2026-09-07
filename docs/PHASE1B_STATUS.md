# Phase 1b — Self-Correction Status

## Implemented in this branch

- Structured SFT failure taxonomy.
- Failure classification from existing SFT `meta_tag` / reason text.
- Bounded reframe planning with a hard default retry budget of 2.
- Explicit learning signals that are **not trusted as knowledge by default**.
- Ethical failures produce safe-alternative framing rather than execution instructions.
- Evidence gaps explicitly request evidence or abstention.
- Regression tests for taxonomy, budget exhaustion, ethical safety, and evidence-gap handling.

## Still required before Phase 1b is complete

1. Persist structured learning signals in Fractal Memory.
2. Connect failure → reframe → retry to the executive cognitive loop.
3. Add retry lineage using `parent_cycle_id` and depth.
4. Add post-retry evaluation and correction-success metrics.
5. Add oscillation / repeated-failure detection.
6. Prove that FailFast, ANLA, Ethics and Agency boundaries remain invariant during retries.

## Status discipline

This document describes implementation work in progress. It does not claim that ANNE learns autonomously, is conscious, or improves empirically until the remaining integration and evaluation work is completed.
