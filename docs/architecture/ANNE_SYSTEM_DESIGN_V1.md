# ANNE System Design v1

**Status:** ARCHITECTURE BASELINE / EXPERIMENTAL IMPLEMENTATION  
**Date:** 2026-09-05

## 1. System principle

ANNE is a cognitive orchestration system around one or more model providers. It is not declared AGI. The architecture is designed to investigate whether perception, memory, exploration, reasoning, values, verification and experience-driven adaptation can be composed into a more reliable artificial cognitive loop.

> **Human-like cognitive organization; machine-native computation.**

Human-like describes the organization of functions, not a claim of biological consciousness or human equivalence.

## 2. Layer model

```text
EXTERNAL WORLD / USER / TOOLS
            │
            ▼
     PERCEPTION / DUY
            │
            ▼
     CONTEXT / BAK + GÖR
            │
     ┌──────┼───────────────────────────┐
     │      │           │               │
   MEMORY  WORLD      MITOS          REASONING
     │     MODEL       │           Math / Physics
     │      │          │               │
     └──────┴──────────┴───────────────┘
                    │
                    ▼
          GLOBAL COGNITIVE WORKSPACE
                    │
             competition/broadcast
                    │
                    ▼
          ANLA / DELIBERATION
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        VALUE     PLANNING  METACOGNITION
          │         │         │
          └─────────┼─────────┘
                    ▼
             HİSSET / EVALUATE
                    │
                    ▼
                 YAP / ACTION
                    │
             safety + policy gate
                    │
                    ▼
              EXTERNAL ACTION
                    │
                    ▼
             OBSERVATION / RESULT
                    │
                    ▼
          PREDICTION ERROR / EVIDENCE
                    │
                    ▼
            EXPERIENCE CONSOLIDATION
                    │
              ┌─────┴─────┐
              ▼           ▼
           MEMORY       STRATEGY
              │           │
              └─────┬─────┘
                    ▼
                 MITOS ↺
```

## 3. DUY–BAK–GÖR–ANLA–HİSSET–YAP

The six stages are the cognitive protocol, not a requirement that every subsystem execute serially.

- **DUY:** acquire input/observations.
- **BAK:** establish context and retrieve relevant experience.
- **GÖR:** allocate attention, detect patterns and preserve important uncertainty.
- **ANLA:** reason, compare hypotheses, construct explanations and predictions.
- **HİSSET:** evaluate affected entities, values, uncertainty and consequences.
- **YAP:** select and execute an authorised action.

Submodules may operate concurrently and publish candidate states into the Global Cognitive Workspace.

## 4. MITOS: exploration layer

MITOS is intentionally lower-depth and higher-throughput than the executive reasoning layer. Its purpose is to search the possibility space without becoming an independent actor.

Modes:

1. EXPLORE — alternatives and neglected routes.
2. COMBINE — recombination of capabilities/variables.
3. INVERT — reverse assumptions and sequences.
4. SIMULATE — lightweight scenario construction.

MITOS can generate many candidates, but quantity is not assumed to be beneficial. Benefit must be demonstrated by improved selection, discovery value, calibration, transfer or computational efficiency.

### Agency boundary

> **Free in ideation; bounded in agency.**

MITOS cannot independently call external tools, contact people, spend money, modify production systems or commit irreversible actions. ANNE's safety/policy gate controls transition from hypothesis to test/action.

## 5. Global Cognitive Workspace

The workspace is the integration point for competing subsystem proposals. Sources can include MITOS, memory, world model, perception, symbolic reasoning, planning and value evaluation.

Each published item carries at minimum:

- source;
- content;
- salience;
- confidence;
- novelty;
- risk.

The workspace is capacity-bounded so that broadcast remains selective rather than becoming an unbounded message bus.

## 6. Intrinsic Discovery Drive

Intrinsic discovery is implemented as a bounded research objective rather than an assumption of consciousness or biological motivation.

The drive asks:

```text
What is uncertain?
        ↓
What would be useful to know?
        ↓
What can be tested cheaply and safely?
        ↓
MITOS exploration
        ↓
ANNE selection
        ↓
experiment / observation
```

Low-probability/high-value candidates remain eligible when expected harm and test cost are low and reversibility/information gain are high.

## 7. World model and counterfactual computation

The world layer must progress from static context representation toward state → prediction → observation comparison.

```text
WORLD STATE
   ↓
COUNTERFACTUAL HYPOTHESIS
   ↓
MATH / PHYSICS / SYMBOLIC / SIMULATION
   ↓
PREDICTION
   ↓
OBSERVATION
   ↓
ERROR
```

Simulation output is tagged as simulation and never promoted to fact without appropriate evidence.

## 8. Reasoning and verification

The language model is a reasoning/generation component, not the sole verifier. Deterministic computation, symbolic derivation, dimensional checks, domain-specific tests, provenance and independent evaluation are preferred wherever applicable.

Claims must retain provenance and status such as:

`HYPOTHESIS | PREDICTION | OBSERVATION | SIMULATION | VERIFIED | FAILED | INCONCLUSIVE`

## 9. Value, safety and ethics

ANNE separates two concepts:

### Immutable safety boundary

Hard constraints governing prohibited or unsafe external actions.

### Learned value model

A research component that can update preferences or prioritisation from evidence without overriding immutable safety constraints.

Ethical scores are not treated as proof of moral understanding.

## 10. Metacognition

Metacognition monitors:

- uncertainty;
- prediction error;
- strategy performance;
- resource/time cost;
- failure patterns;
- applicability of learned rules.

The first form of self-modification is strategy adaptation, not unrestricted source-code rewriting.

A strategy may gain or lose selection priority according to measured outcomes.

## 11. Experience-driven learning

Experience is not equivalent to storage.

```text
HYPOTHESIS
   ↓
PREDICTION
   ↓
TEST
   ↓
OBSERVATION
   ↓
PREDICTION ERROR
   ↓
EXPERIENCE RECORD
   ↓
RULE / BELIEF / STRATEGY UPDATE
   ↓
TRANSFER TEST
```

A learning claim requires measurable future behavioural change, appropriate transfer and revision when evidence contradicts the learned pattern.

The experience schema must keep predicted and observed outcomes separate.

## 12. Time and continuity

The architecture treats ANNE as a persistent process rather than only a request/response function. Experience may be consolidated during scheduled or offline cycles, while online decisions remain bounded by current state and safety policy.

Dream Cycle is therefore interpreted as an experimental consolidation/replay mechanism, not evidence of human-like dreaming or consciousness.

## 13. Embodiment boundary

Physical embodiment is not required for the current research baseline. However, the architecture exposes an environment/action/observation boundary so that virtual environments, IoT devices or robotics can later provide sensorimotor experience without rewriting the cognitive core.

## 14. Core lifecycle

```text
GOAL / OBSERVATION
      ↓
DUY → BAK → GÖR
      ↓
WORKSPACE
      ↓
MITOS + MEMORY + WORLD + REASONING
      ↓
ANLA
      ↓
HİSSET / VALUE / SAFETY
      ↓
PLAN
      ↓
YAP
      ↓
VERIFY
      ↓
OBSERVE RESULT
      ↓
EXPERIENCE
      ↓
LEARN / CONSOLIDATE
      ↓
UPDATED MEMORY + STRATEGY + MITOS GUIDANCE
      ↺
```

## 15. Implementation status

### IMPLEMENTED in this branch

- bounded MITOS generator with four exploration modes;
- deterministic/reproducible candidate generation for experiments;
- explicit hypothesis candidate schema;
- Global Cognitive Workspace primitive;
- MITOS → ANNE proposal loop;
- experience lifecycle record with prediction error;
- discovery-drive shortlist gate;
- unit tests for the new primitives.

### EXPERIMENTAL

- discovery-value scoring;
- workspace priority scoring;
- intrinsic-discovery formulation;
- strategy adaptation;
- real-world experiment loop;
- world-model integration;
- learning effectiveness.

### NOT CLAIMED

- AGI;
- consciousness;
- human-equivalent reasoning;
- autonomous self-modification;
- real-world learning from simulated outcomes;
- zero hallucination;
- guaranteed moral reasoning.

## 16. Research gates

Every future expansion should pass these gates:

1. **Safety:** no unapproved external agency.
2. **Evidence:** simulated and observed outcomes remain separate.
3. **Reproducibility:** benchmark inputs, seeds and metrics are recorded.
4. **Ablation:** compare ANNE with and without the proposed subsystem.
5. **Learning:** show future behavioural change, not merely stored records.
6. **Transfer:** test on related tasks not used for the update.
7. **Contradiction:** wrong predictions must weaken or revise beliefs/rules.
8. **Cost:** measure latency, compute and memory overhead.

## 17. Primary research question

> **Can a bounded exploratory subsystem (MITOS), integrated through a competitive global workspace and an evidence-driven experience loop, measurably improve ANNE's discovery, decision quality, calibration, transfer and computational efficiency without increasing unacceptable risk?**

That question is the boundary between the architecture and any future AGI hypothesis.
