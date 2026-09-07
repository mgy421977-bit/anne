# ANNE Runtime Architecture v0.3

## Purpose

The repository now has the architectural primitives for ANNE. This document
marks the transition from isolated primitives to one executable, bounded
cognitive runtime.

## Runtime loop

```text
SEN / INPUT
    ↓
OBSERVE
    ↓
GLOBAL COGNITIVE WORKSPACE
    ↓
MEMORY CONTEXT ───────────────┐
    ↓                         │
MITOS EXPLORATION             │
    ↓                         │
MODEL REASONING ←─────────────┘
    ↓
PREDICTION / PLAN
    ↓
AGENCY GATE
    ├── DENY / BLOCK
    ├── REVIEW
    └── ALLOW → explicit executor
                    ↓
                 OUTCOME
                    ↓
              PREDICTION ERROR
                    ↓
               EXPERIENCE
                    ↓
                LEARNING
                    ↺
```

## Evidence boundary

A generated model response is not an observed outcome. The v0.3 runtime records
that distinction explicitly (`observed=False`) so that memory storage cannot be
mistaken for learning. Durable learning requires a later independently observed
outcome and an explicit future-behavior change.

MITOS candidates are exploratory hypotheses. They can expand the search space,
but they cannot authorize actions or promote claims to FACT.

## Agency boundary

External actions are disabled by default. Even when explicitly enabled, an
`ActionProposal` must pass `AgencyGate` and an executor must be explicitly
configured. The runtime never treats model confidence as authorization.

## Hardware boundary

The runtime consumes a minimal `ModelAdapter` contract. It does not assume CPU,
GPU, NPU, quantum, or hybrid hardware. Compute selection remains the responsibility
of `ComputeGovernor` and its explicit executors.

## What v0.3 does not do yet

- It does not claim autonomous learning from a single response.
- It does not grant MITOS operational authority.
- It does not perform uncontrolled self-modification.
- It does not silently create unlimited agents or consume unlimited resources.
- It does not replace the existing tool-using `AnneAgent`; integration will be
  introduced through explicit adapters rather than a risky rewrite.

## Next runtime stages

1. Add provider adapter integration for the existing local/Tinker path.
2. Replace the temporary local memory context with the provider-neutral storage
   and FractalMemory abstractions where appropriate.
3. Add real observation adapters and measured prediction-error capture.
4. Connect MITOS specialist missions through ResourceGovernor budgets.
5. Add experience promotion and transfer tests.
6. Add sandbox/shadow/canary execution for bounded self-improvement.
7. Only after those gates are tested, enable selected autonomous operations.
