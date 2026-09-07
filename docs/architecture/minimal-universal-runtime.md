# ANNE Minimal Universal Runtime

**Status: IMPLEMENTED principle / EXPERIMENTAL runtime profile**

## Axiom 0

> **ANNE shall operate with the minimum sufficient computational resources available on its host substrate while preserving its invariant cognitive, safety, provenance, semantic, and agency boundaries.**

Available capacity may expand the amount of bounded exploration, memory retrieval, parallel proposal generation, or recursive reasoning. It must never change the meaning of the safety and authorization boundaries.

## Substrate independence

ANNE is designed as one cognitive architecture with substrate-specific runtime adapters, not as separate cognitive systems:

```text
                    ANNE Cognitive Core
                           │
                 Substrate / Resource API
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      Classical         Quantum        Bio-Quantum
       runtime          runtime          runtime
```

The current repository implements the **resource-profile abstraction** only. Quantum and bio-quantum execution backends remain **HYPOTHESIS / ROADMAP** until an actual hardware integration exists and is experimentally validated.

## Minimum sufficient computation

The runtime should scale *within explicit budgets*:

```text
Host capacity
     ↓
Capability detection
     ↓
ResourceProfile
     ↓
Bounded cognitive budget
     ↓
ANNE Core
```

A small laptop should therefore be able to execute a minimal ANNE cycle. A larger host may receive a larger bounded budget. A future accelerator may provide specialized operations without becoming the source of cognitive authority.

### Invariants

These do not scale away:

1. FailFast remains mandatory.
2. Semantic/ANLA validation remains mandatory where configured.
3. Ethical constraints remain mandatory.
4. Evidence and provenance discipline remain mandatory.
5. MITOS proposes; ANNE selects and validates.
6. Cognition does not equal authorization.
7. Agency Gate remains independent of available compute.
8. Recursion and retry remain hard-bounded.
9. Confidence never becomes truth merely because more compute is available.
10. More hardware must not silently grant more authority.

## What may scale

Subject to hard limits and empirical validation:

- number of MITOS candidates;
- retrieval breadth/depth;
- reasoning budget;
- bounded fractal depth;
- bounded retry budget;
- specialist parallelism;
- offline consolidation capacity.

Scaling is an optimization of available computation, not a change to the architecture's safety contract.

## Research status

**IMPLEMENTED:** substrate enum and bounded `ResourceProfile` abstraction.

**EXPERIMENTAL:** using resource profiles to tune cognitive budgets.

**HYPOTHESIS:** the same ANNE cognitive invariants can be efficiently mapped to quantum or bio-quantum substrates.

**ROADMAP:** implement and benchmark concrete accelerator adapters only when real hardware/software interfaces are available.

No claim is made here that quantum or bio-quantum hardware provides consciousness, general intelligence, or superior cognition.
