# ANNE × MITOS Cognitive Architecture

**Status:** HYPOTHESIS / ARCHITECTURE PROPOSAL  
**Version:** 0.1  
**Date:** 2026-09-05

## 1. Purpose

This document defines a research architecture for connecting **MITOS** to ANNE as a bounded hypothesis-generation and experience-production subsystem.

The central idea is:

> **MITOS generates possibilities. ANNE evaluates possibilities. Computation tests them. Reality supplies outcomes. Memory learns from the difference.**

MITOS is not a second decision-maker and is not granted direct real-world agency.

## 2. Architectural roles

### ANNE Core

ANNE is the executive/orchestration layer. It integrates perception, context, memory, semantic processing, planning, evaluation, verification, safety, decision and action.

The existing six-stage conceptual loop remains:

`DUY → BAK → GÖR → ANLA → HİSSET → YAP`

### MITOS

MITOS is the exploration layer. It deliberately has less reasoning depth than the ANNE executive layer but can generate a large and diverse hypothesis space.

Primary modes:

- **EXPLORE** — generate alternative hypotheses;
- **COMBINE** — recombine concepts or variables;
- **INVERT** — search from an opposite or reversed assumption;
- **SIMULATE** — construct lightweight candidate scenarios.

MITOS may be broad in internal ideation while remaining strictly bounded in external capability.

### Computation layer

Deterministic numerical, symbolic, derivation, dimensional and physics-oriented components test hypotheses where applicable. A simulation result is not automatically a fact.

### Reality / observation

Where an experiment or external observation is possible, the observed outcome is kept separate from the prediction.

### Fractal / episodic memory

Predictions, observations, outcomes, errors and provenance become experience records. Failed predictions are retained as learning evidence rather than silently discarded.

## 3. Cognitive loop

```text
GOAL
  ↓
DATA / OBSERVATION
  ↓
PRE-ANALYSIS
  ↓
UNKNOWN VARIABLES
  ↓
MITOS
  ├─ EXPLORE
  ├─ COMBINE
  ├─ INVERT
  └─ SIMULATE
  ↓
HYPOTHESIS SPACE
  ↓
COMPUTATION / SIMULATION
  ↓
PREDICTIONS
  ↓
ANNE EVALUATION
  ├─ evidence
  ├─ plausibility
  ├─ testability
  ├─ novelty
  ├─ expected benefit
  ├─ cost
  ├─ uncertainty
  └─ ethical / safety constraints
  ↓
SELECT TESTABLE CANDIDATES
  ↓
OBSERVED OUTCOME
  ↓
PREDICTION ERROR
  ↓
EXPERIENCE RECORD
  ↓
MEMORY / LEARNING
  ↓
UPDATED MITOS GUIDANCE
  ↺
```

## 4. Low-probability / high-value search

A key research hypothesis is that ANNE should not rank candidates only by probability of success.

A low-probability candidate can be valuable when:

- potential positive impact is high;
- expected harm is zero or very low;
- test cost is low;
- the experiment is reversible;
- information gain is high;
- the idea is sufficiently novel.

A candidate score can therefore be represented conceptually as:

`DiscoveryValue = f(expected_benefit, novelty, information_gain, testability, cost, harm_risk, uncertainty)`

The exact scoring function is an experimental variable, not a settled claim.

## 5. Ethical boundary

MITOS is **free to generate hypotheses inside its sandbox**, but it is not free to execute external actions.

The principle is:

> **Free in ideation; bounded in agency.**

ANNE retains the decision authority for any transition from hypothesis to experiment or action.

The existing research concepts of **İyilik ve Eşitlik**, **Etik Kontrol**, and **Empati** can operate as evaluation dimensions. They should not be represented as scientifically validated moral reasoning merely because a prototype assigns scores to them.

## 6. Experience schema

A minimal experience record should distinguish hypothesis from fact:

```json
{
  "experience_id": "M-000001",
  "hypothesis": "...",
  "status": "HYPOTHESIS",
  "predicted_probability": 0.12,
  "confidence": 0.31,
  "novelty": 0.90,
  "testability": 0.80,
  "expected_benefit": 0.95,
  "harm_risk": 0.00,
  "test_cost": 0.02,
  "prediction": "...",
  "observation": null,
  "outcome": null,
  "prediction_error": null,
  "provenance": []
}
```

Possible lifecycle:

`HYPOTHESIS → PREDICTION → TESTED → VERIFIED | FAILED | INCONCLUSIVE`

A failed or inconclusive result remains an experience record.

## 7. Learning hypothesis

The intended learning loop is not merely memory storage.

Evidence for learning should require, where applicable:

1. repeated experience;
2. a measurable update to a rule, belief, routing policy or generator guidance;
3. transfer to a related new problem;
4. appropriate rejection when the learned pattern does not apply;
5. weakening or revision after incorrect predictions.

A larger MITOS output volume is therefore only useful if increased diversity and experience quality improve ANNE's later decisions or reduce the computation required to reach comparable outcomes.

## 8. Research question

The primary test is:

> **Does increasing the quantity and diversity of MITOS-generated experience improve ANNE's decision quality, discovery value, calibration, or computational efficiency under controlled conditions?**

A stronger result would demonstrate a relationship between:

`MITOS experience volume/diversity ↑ → ANNE selection quality ↑ and/or decision cost ↓`

This is a hypothesis to benchmark, not a current capability claim.

## 9. First controlled experiment

Initial task:

> **Find a legal, ethical, zero-capital method for creating economic value.**

Procedure:

1. MITOS receives the goal without a predefined candidate list.
2. MITOS generates a bounded batch of hypotheses.
3. ANNE evaluates the batch without treating MITOS output as truth.
4. Candidates are ranked by probability, benefit, novelty, testability, cost and harm risk.
5. Low-probability/high-value candidates remain eligible when testing cost and harm are sufficiently low.
6. The selected candidates are tested where practical.
7. Outcomes are recorded separately from predictions.
8. The prediction error becomes experience data.
9. A subsequent MITOS batch is generated using only the permitted learned guidance.
10. The experiment compares later performance against earlier batches and against baselines.

## 10. Relationship to earlier ANNE concepts

The architecture preserves the earlier ANNE concepts rather than replacing them:

- **İAM** — communication/context interpretation;
- **Damaris** — security and protected information handling;
- **MIRA** — semantic, symbolic and expressive interpretation;
- **MIRA Genesis** — future-oriented scenario generation;
- **AEON** — ethical/empathetic/organic integration concept;
- **İyilik ve Eşitlik** — foundational value dimension;
- **Bilimsel Keşif ve Merak** — discovery objective;
- **Etik Kontrol** — decision gate;
- **Empati** — social/contextual evaluation;
- **DUY–BAK–GÖR–ANLA–HİSSET–YAP** — cognitive processing loop.

These names describe the project's conceptual lineage. Their scientific validity must be established independently through implementation and experiments.

## 11. Implementation rule

Do not rebuild the ANNE core merely to add MITOS.

The first implementation should be a bounded experimental layer that plugs into existing interfaces for:

- hypothesis/proposal generation;
- simulation;
- memory/experience recording;
- evaluation;
- verification;
- benchmark logging.

New capabilities must be labelled **IMPLEMENTED**, **EXPERIMENTAL**, **HYPOTHESIS**, or **ROADMAP** according to the repository's research-discipline rules.
