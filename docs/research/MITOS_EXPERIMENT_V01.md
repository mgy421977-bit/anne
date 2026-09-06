# MITOS Experiment v0.1 — Low-Probability / High-Value Discovery

**Status:** HYPOTHESIS / EXPERIMENT DESIGN  
**Date:** 2026-09-05

## Objective

Test whether a bounded, high-volume hypothesis generator can improve ANNE's later selection and learning without requiring the executive layer to deeply deliberate over every candidate.

## Task

Generate legal, ethical and zero-capital ways to create economic value.

The experiment is intentionally open-ended. No predefined candidate list is supplied to MITOS.

## Two-stage protocol

### Stage 1 — MITOS exploration

MITOS generates a bounded batch of candidates using:

- exploration;
- recombination;
- inversion of assumptions;
- lightweight scenario construction.

Each candidate is represented as a hypothesis, not a fact.

### Stage 2 — ANNE evaluation

ANNE evaluates each candidate using explicit dimensions:

- expected positive impact;
- harm risk;
- legality/safety constraints;
- test cost;
- reversibility;
- novelty;
- testability;
- predicted probability;
- uncertainty;
- information gain.

The experiment specifically preserves candidates with low predicted probability when their potential benefit is high and their testing cost and harm risk are sufficiently low.

## Outcome loop

```text
MITOS hypothesis
      ↓
probability + prediction
      ↓
ANNE selection
      ↓
experiment / observation
      ↓
actual outcome
      ↓
prediction error
      ↓
experience record
      ↓
learning update
      ↓
next MITOS batch
```

## Required measurements

At minimum, compare multiple batch sizes such as 10, 100 and 1,000 candidates where resources permit.

Measure:

- candidate diversity;
- novelty;
- proportion surviving safety/ethical screening;
- top-k selection quality;
- calibration of predicted probabilities;
- information gain;
- successful test rate;
- prediction error;
- repeated-task transfer;
- computation/time per selected candidate.

The key hypothesis is not that more candidates are automatically better. The test is whether additional **useful experience diversity** improves later selection or reduces the resources required to achieve comparable quality.

## Negative controls

The experiment should compare MITOS against at least one simpler baseline, such as:

- random candidate generation;
- a single-pass model-generated shortlist;
- ANNE evaluation without MITOS expansion.

## Learning criterion

A run should not be called learning merely because records accumulate.

Evidence of learning requires a measurable change that improves performance on a later, related task and appropriate degradation/revision when the learned pattern is contradicted by outcomes.

## Safety rule

MITOS has no direct external agency in this experiment. It can generate and simulate hypotheses inside a sandbox. ANNE controls any transition to external testing or action.

## Expected research result

Possible outcomes are all informative:

1. **Positive:** larger/diverse MITOS experience improves ANNE selection or efficiency.
2. **Neutral:** additional candidates provide little benefit beyond a smaller batch.
3. **Negative:** more candidates increase computation without improving decisions.
4. **Misleading:** MITOS produces attractive but systematically miscalibrated low-probability ideas.

The experiment should preserve all four possibilities rather than assuming the desired result.
