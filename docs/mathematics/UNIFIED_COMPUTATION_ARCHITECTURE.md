# ANNE Unified Computation Architecture

This document records the deterministic computation layer assembled on the current language/online-learning base.

## Flow

Language/cognitive runtime → numerical math → symbolic math → derivation trace → independent verification → dimensional validation → physics/orbital calculation.

## Components

- `anne.core.derivation_engine.DerivationEngine`: auditable elimination derivations with explicit steps.
- `anne.core.symbolic_math_engine.SymbolicMathEngine`: symbolic parsing, isolation, substitution, simplification and relation verification.
- `anne.core.units.Units`: M/L/T dimensional primitives and compatibility checks.
- `anne.physics`: constants, classical kinematics and two-body orbital primitives.
- `anne.math.physics_bridge`: typed bridge from deterministic mathematics to Earth circular-orbit calculation.

## Benchmark #01

Inputs:

- `v = u + a*t`
- `s = u*t + (1/2)*a*t**2`

The target relation is held as an independent verification oracle rather than supplied to the derivation algorithm. The engine must isolate `t`, substitute, expand and simplify before verification.

This demonstrates derivation capability; it does **not** by itself demonstrate learning, transfer, or persistent memory.
