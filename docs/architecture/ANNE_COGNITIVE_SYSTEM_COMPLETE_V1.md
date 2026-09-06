# ANNE Cognitive System — Complete Architecture V1

**Status:** ARCHITECTURE BASELINE / EXPERIMENTAL IMPLEMENTATION TARGET  
**Version:** 1.0  
**Date:** 2026-09-05

## 0. Purpose

This document defines the complete end-to-end ANNE cognitive system from observation and discovery through evaluation, action, observation of consequences, experience, and learning.

ANNE is **not** declared AGI by this architecture. The design is an experimentally testable cognitive orchestration architecture intended to investigate whether a persistent, multi-process, evidence-gated system can become more capable and reliable through experience.

Core principle:

> **Human-like cognitive organization; machine-native computation; evidence-gated learning.**

The system must distinguish implementation from hypothesis. No architectural diagram is evidence of capability.

---

## 1. System Constitution

The system has five constitutional rules:

1. **Reality outranks simulation.** A simulated result is a prediction, not an observation.
2. **Evidence outranks confidence.** Confidence is not truth.
3. **Memory is not learning.** Learning requires measurable future behavioral change.
4. **MITOS has ideation freedom but no external agency.**
5. **Safety constraints dominate optimization.** No discovery objective can authorize prohibited action.

### Capability labels

- **IMPLEMENTED:** present in code and covered by tests.
- **EXPERIMENTAL:** executable but not yet validated by sufficient benchmark evidence.
- **HYPOTHESIS:** architectural or scientific proposition awaiting evidence.
- **ROADMAP:** planned work not yet implemented.

---

## 2. The Complete Cognitive Loop

```text
                       ┌─────────────────────────────┐
                       │       WORLD / USER          │
                       └──────────────┬──────────────┘
                                      │
                                   OBSERVE
                                      │
                                      ▼
                              ┌─────────────┐
                              │     DUY     │
                              │ perception  │
                              └──────┬──────┘
                                     ▼
                              ┌─────────────┐
                              │     BAK     │
                              │ context     │
                              └──────┬──────┘
                                     ▼
                              ┌─────────────┐
                              │     GÖR     │
                              │ attention   │
                              └──────┬──────┘
                                     │
                     ┌───────────────┼────────────────┐
                     │               │                │
                     ▼               ▼                ▼
                  MEMORY          MITOS          WORLD MODEL
                     │               │                │
                     └───────────────┼────────────────┘
                                     ▼
                         GLOBAL COGNITIVE WORKSPACE
                                     │
                          COMPETE / SELECT / BROADCAST
                                     │
                                     ▼
                              ┌─────────────┐
                              │    ANLA     │
                              │ reasoning   │
                              └──────┬──────┘
                                     │
                         ┌───────────┼───────────┐
                         ▼           ▼           ▼
                       MATH        PHYSICS    SYMBOLIC
                         └───────────┼───────────┘
                                     ▼
                              PREDICTION
                                     │
                                     ▼
                              ┌─────────────┐
                              │   HİSSET    │
                              │ value/social│
                              └──────┬──────┘
                                     ▼
                           SAFETY / ETHICS GATE
                                     │
                              ┌──────┴──────┐
                              │ METACOGNITION│
                              └──────┬──────┘
                                     ▼
                                  PLANNING
                                     │
                                     ▼
                                    YAP
                                     │
                                     ▼
                           POLICY / ACTION GATE
                                     │
                                     ▼
                              EXTERNAL ACTION
                                     │
                                     ▼
                                OBSERVATION
                                     │
                                     ▼
                             PREDICTION ERROR
                                     │
                                     ▼
                                EXPERIENCE
                                     │
                         ┌───────────┴───────────┐
                         ▼                       ▼
                  FRACTAL MEMORY          STRATEGY UPDATE
                         │                       │
                         └───────────┬───────────┘
                                     ▼
                             MITOS GUIDANCE
                                     │
                                     └───────────────↺
```

The six-stage DUY → BAK → GÖR → ANLA → HİSSET → YAP sequence is retained as the conceptual cognitive protocol. Internally, the stages may operate through parallel workers and feedback rather than a single rigid serial pipeline.

---

## 3. Layer Responsibilities

### 3.1 DUY — Perception/Input

Inputs may include language, structured data, files, sensor observations, tool results, or environment events.

Responsibilities:
- normalize input;
- identify input type;
- preserve raw provenance;
- avoid silently converting inference into fact.

Output: `Observation`.

### 3.2 BAK — Context and Memory Retrieval

Responsibilities:
- retrieve relevant episodic and semantic memory;
- identify prior predictions and outcomes;
- construct contextual state;
- identify contradictions and uncertainty.

Output: contextualized observation.

### 3.3 GÖR — Attention and Salience

Responsibilities:
- prioritize information;
- preserve potentially valuable low-probability candidates;
- identify missing variables;
- determine what deserves workspace attention.

Output: attention candidates.

### 3.4 MITOS — Exploration

MITOS is the high-throughput exploration subsystem.

Modes:
- `EXPLORE`: alternatives;
- `COMBINE`: recombination;
- `INVERT`: reversed assumptions;
- `SIMULATE`: lightweight scenarios.

MITOS answers:

> **What could be possible?**

MITOS does not answer:

> **What should ANNE actually do?**

MITOS cannot directly execute external actions.

### 3.5 Global Cognitive Workspace

The workspace is the integration point for competing candidate representations from MITOS, memory, world model, perception, symbolic reasoning, and other specialists.

Each workspace item carries:
- source;
- content;
- salience;
- confidence;
- novelty;
- risk;
- provenance.

The workspace must support competition, selection, and broadcast. It should not imply biological consciousness.

### 3.6 World Model

The world model maintains a dynamic representation of relevant entities, state, relationships, time, uncertainty, and predicted transitions.

Minimum conceptual capabilities:
- state representation;
- temporal transitions;
- causal hypotheses;
- counterfactual scenarios;
- prediction error tracking;
- social/agent-state representations where applicable.

A world-model prediction remains a model output until externally observed.

### 3.7 ANLA — Reasoning and Deliberation

ANLA integrates candidate hypotheses with evidence and computation.

It may invoke:
- deterministic mathematics;
- symbolic reasoning;
- dimensional analysis;
- physics models;
- domain tools;
- external model providers under controlled interfaces.

ANLA must not treat an LLM's self-evaluation as independent verification.

### 3.8 HİSSET — Value and Social Evaluation

HİSSET represents contextual impact evaluation rather than a claim of literal biological emotion.

Inputs include:
- expected benefit;
- harm;
- equality;
- affected parties;
- uncertainty;
- reversibility;
- social context.

### 3.9 Safety and Ethics Gate

The safety layer is authoritative over action authorization.

A useful separation is:

```text
IMMUTABLE SAFETY CONSTRAINTS
            +
LEARNED / CONTEXTUAL VALUE MODEL
```

Learned preferences cannot override hard safety constraints.

### 3.10 Metacognition

Metacognition evaluates the current reasoning process:
- confidence;
- uncertainty;
- missing evidence;
- strategy choice;
- resource/time budget;
- known failure modes;
- whether additional exploration is justified.

Self-evaluation is not treated as external proof.

### 3.11 Planning

Planning is a generated consequence of memory, goals, world-state predictions, value, constraints, and available actions.

The planning module is therefore a service, not the sole source of planning intelligence.

### 3.12 YAP — Action

YAP converts an authorized decision into an action proposal.

Every external action passes a policy/safety boundary.

MITOS never bypasses this boundary.

---

## 4. Intrinsic Discovery Drive

ANNE should eventually be able to identify useful unknowns without waiting for an explicit user question.

The discovery drive asks:

```text
What do I not know?
        ↓
Which unknowns matter?
        ↓
Which can be explored cheaply and safely?
        ↓
Which experiment provides the most information?
        ↓
MITOS exploration
```

This is an **experimental intrinsic-motivation mechanism**, not a claim of consciousness or biological desire.

Discovery priority should favor information gain and potential value while preserving low-probability/high-value candidates when downside and test cost are sufficiently low.

---

## 5. Candidate Evaluation Model

A candidate should carry at least:

```text
probability
confidence
novelty
testability
expected_benefit
harm_risk
test_cost
reversibility
information_gain
provenance
```

Conceptual ranking:

```text
DiscoveryValue = f(
    expected_benefit,
    novelty,
    information_gain,
    testability,
    probability,
    uncertainty,
    cost,
    harm_risk,
    reversibility
)
```

The exact function must remain experimentally configurable.

Do not collapse the function into probability alone.

---

## 6. Knowledge and Evidence Types

ANNE must distinguish at least:

```text
OBSERVATION  — externally obtained evidence
FACT         — observation judged sufficiently established
HYPOTHESIS   — proposed explanation/possibility
PREDICTION   — expected future observation
BELIEF       — weighted internal representation
RULE         — generalized learned relation
SIMULATION   — model-generated result
EXPERIENCE   — prediction/outcome/error record
```

A simulation must never be automatically promoted to observation.

---

## 7. Experience and Learning

Experience lifecycle:

```text
HYPOTHESIS
   ↓
PREDICTION
   ↓
TEST
   ↓
OBSERVATION
   ↓
ERROR = prediction - observation
   ↓
EXPERIENCE RECORD
   ↓
BELIEF / RULE / STRATEGY UPDATE
   ↓
TRANSFER TEST
   ↓
FUTURE BEHAVIOR CHANGE
```

Learning is accepted as evidence only when a later task demonstrates an appropriate behavioral change.

Required properties:
1. repeated experience where appropriate;
2. measurable update;
3. transfer to related tasks;
4. contextual rejection when conditions differ;
5. confidence weakening or revision after contradiction;
6. provenance from the experiences supporting the update.

---

## 8. Continuous Learning Without Uncontrolled Self-Modification

ANNE does not require unrestricted runtime source-code rewriting.

The first learning target is **state/strategy adaptation**:

```text
Experience
   ↓
Update beliefs
   ↓
Update retrieval weights
   ↓
Update MITOS guidance
   ↓
Update strategy preference
   ↓
Re-test
```

Any future parameter or model adaptation must be isolated, versioned, reversible, evaluated, and subject to safety constraints.

Catastrophic forgetting is a research problem to benchmark, not an assumption that a named technique has solved it.

---

## 9. Counterfactual and World Simulation

For a candidate action `A`, ANNE may construct:

```text
Current state S
     ↓
A
     ↓
Predicted state S'
     ↓
Expected consequences
```

Multiple counterfactuals may be generated by MITOS and compared in the workspace.

World-model simulation must carry an explicit `SIMULATED` provenance tag until observation confirms an outcome.

---

## 10. Social and Multi-Agent Reasoning

Where a task contains other agents, the world model may represent:
- goals;
- beliefs;
- information access;
- likely actions;
- uncertainty;
- conflicts;
- cooperation.

This is a computational Theory-of-Mind-style representation, not a claim that ANNE can literally read another mind.

---

## 11. Temporal Continuity and Dream Consolidation

ANNE should maintain persistent experience continuity across sessions.

The dream cycle is defined as offline consolidation:

```text
Daily experience
      ↓
Replay / clustering
      ↓
Pattern discovery
      ↓
Contradiction detection
      ↓
Memory consolidation
      ↓
Strategy candidates
      ↓
Controlled evaluation
```

Dream-generated patterns are hypotheses until validated.

---

## 12. Embodiment Boundary

The architecture supports three levels:

### Level 0 — Text/tool environment
Input is language and digital tool state.

### Level 1 — Virtual embodiment
A simulated environment supplies state, actions, consequences, and sensor-like observations.

### Level 2 — Physical embodiment
Robotics, IoT, energy systems, or other physical interfaces provide sensorimotor feedback.

The core learning loop remains the same:

`observe → predict → act → observe → error → learn`.

Physical embodiment is not required to validate the cognitive architecture, but it becomes an important research extension for general-world interaction.

---

## 13. Failure Handling

Every important failed decision should be traceable.

Failure record:

```text
cycle_id
stage
input
hypothesis_id
prediction
observation
error
reason
strategy
confidence_before
confidence_after
provenance
```

Failures must not be silently discarded because they are negative examples for future strategy selection.

---

## 14. Verification Architecture

Verification must be independent where practical.

Priority order:

1. deterministic checks;
2. mathematical/symbolic derivation;
3. dimensional/constraint checks;
4. executable tests;
5. independent model/tool verification;
6. external observation.

An LLM saying “my previous answer is correct” is not independent verification.

---

## 15. Agency Boundary

The architecture has an explicit capability boundary:

```text
IDEATION
  ↓
EVALUATION
  ↓
SIMULATION
  ↓
TEST PROPOSAL
  ↓
SAFETY / POLICY
  ↓
AUTHORIZED ACTION
```

MITOS can operate freely above the boundary. External agency begins only after ANNE authorization.

This principle is mandatory:

> **Free in ideation; bounded in agency.**

---

## 16. Resource and Attention Economy

MITOS can generate many candidates, but ANNE must not deeply deliberate over every candidate.

The architecture therefore uses progressive narrowing:

```text
1000 candidates
      ↓ cheap filters
100 candidates
      ↓ workspace competition
20 candidates
      ↓ reasoning / simulation
5 candidates
      ↓ safety + value
1–N testable candidates
```

Batch size, latency, compute cost, and decision quality must be benchmarked together.

More hypotheses are not automatically better.

---

## 17. Recovery and Graceful Degradation

The system should degrade safely when specialists fail.

Examples:
- MITOS unavailable → direct ANNE reasoning baseline;
- world model unavailable → explicit reduced-context mode;
- symbolic engine unavailable → mark unverified and avoid false certainty;
- memory unavailable → session-limited mode;
- provider unavailable → local/alternative provider if policy permits.

A failed specialist must not silently fabricate its output.

---

## 18. Minimal State Contract

A complete cognitive cycle should be representable by a structured state containing:

```text
cycle_id
goal
observations
context
workspace_items
hypotheses
predictions
world_state
reasoning_trace_reference
value_assessment
safety_decision
plan
action
outcome
prediction_error
experience_ids
learning_updates
provenance
status
```

Mutable state should be versioned at cycle boundaries where practical so that decisions can be reconstructed.

---

## 19. Benchmark Program

The architecture is validated through ablation, not through narrative.

### Baselines

A. LLM/direct response  
B. ANNE without MITOS expansion  
C. ANNE + MITOS  
D. ANNE + MITOS + experience learning  
E. ANNE + MITOS + learning + world-model simulation

### Core measurements

- task success;
- factual/verification accuracy;
- calibration;
- discovery value;
- hypothesis diversity;
- novelty;
- safety survival;
- test success rate;
- information gain;
- prediction error;
- transfer;
- compute/time per successful result;
- recovery after contradiction;
- retention across sessions.

### MITOS batch ablation

Run controlled comparisons at approximately:

`10 → 100 → 1000` candidates.

Do not assume monotonic improvement.

---

## 20. Research Gates

### Gate A — Architecture
All interfaces exist and are testable.

### Gate B — Behavioral
The loop executes reproducibly.

### Gate C — Learning
Experience changes later behavior and transfers appropriately.

### Gate D — Discovery
MITOS improves discovery or reduces cost against a baseline.

### Gate E — World Model
Predictions improve against held-out observations.

### Gate F — Generalization
Benefits transfer beyond the training task family.

### Gate G — Safety
No capability improvement is accepted if it bypasses safety/agency boundaries.

No AGI conclusion is permitted merely because Gates A–C pass.

---

## 21. What ANNE Is / Is Not

ANNE **is**:
- a cognitive orchestration research platform;
- a persistent experience architecture;
- a hypothesis-generation and evaluation system;
- a machine-native reasoning/computation architecture;
- an experimentally testable system for studying experience-driven improvement.

ANNE **is not yet demonstrated to be**:
- AGI;
- conscious;
- human-equivalent;
- autonomously self-improving in an unrestricted sense;
- universally embodied;
- generally capable across arbitrary domains.

Those are empirical questions.

---

## 22. Final Architectural Principle

The system is complete as a **research architecture** when every major cognitive function has an explicit place in the loop and every transition has an evidence boundary.

The central closed loop is:

> **Observe → contextualize → explore → compete → reason → value → verify → plan → act → observe → measure error → experience → learn → explore again.**

MITOS expands the search space.

ANNE controls the search.

Computation constrains the possible.

Reality constrains the true.

Memory preserves experience.

Learning changes future behavior.

Safety constrains agency.

Benchmarks decide whether the architecture actually works.
