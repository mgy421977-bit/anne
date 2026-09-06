# ANNE Unified Computation Architecture

This document records the deterministic **computation layer** design assembled alongside the language/online-learning work. It is an architecture note, not a claim that every listed module is already present on `main`.

## Flow

Language/cognitive runtime → numerical math → symbolic math → derivation trace → independent verification → dimensional validation → physics/orbital calculation.

## Design components

Intended computation stack (module names may live under `src/anne/math/`, `src/anne/physics/`, or related feature branches until merged):

- **Derivation engine** — auditable elimination derivations with explicit steps.
- **Symbolic math engine** — symbolic parsing, isolation, substitution, simplification, and relation verification.
- **Units** — M/L/T dimensional primitives and compatibility checks.
- **Physics** — constants, classical kinematics, and two-body orbital primitives.
- **Math ↔ physics bridge** — typed bridge from deterministic mathematics to Earth circular-orbit calculation.

Related cognitive runtime on `main` (orchestration, not the computation kernel): pipeline, decision/verification gates, memory, offline agent, providers, safety.

## Benchmark #01

Inputs:

- `v = u + a*t`
- `s = u*t + (1/2)*a*t**2`

The target relation is held as an **independent verification oracle** rather than supplied to the derivation algorithm. The engine must isolate `t`, substitute, expand, and simplify before verification.

This demonstrates derivation capability; it does **not** by itself demonstrate learning, transfer, or persistent memory.

## Evidence rule

Aligns with project discipline: a correct calculation is not evidence of learning. Promote components from hypothesis/experimental to implemented only when code, tests, and (where relevant) benchmark artifacts exist on the branch under discussion.
