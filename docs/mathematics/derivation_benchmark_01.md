# ANNE Mathematical Derivation Benchmark #01

**Status:** Specification / checkpoint — implementation not yet claimed.

## Objective

Test whether ANNE can derive a mathematically valid relation from given equations without being given the target result.

The benchmark is intentionally separated from the target oracle: the expected relation is used only for independent evaluation and must not be injected into the reasoning prompt or derivation engine as a known answer.

## Problem

Given:

\[
v = u + at
\]

\[
s = ut + \frac{1}{2}at^2
\]

ANNE must eliminate `t` and derive a relation among `v`, `u`, `a`, and `s`.

### Hidden evaluation target

\[
v^2 = u^2 + 2as
\]

The target is an evaluator oracle, not an input to ANNE.

## Required derivation trace

A successful run should expose an auditable sequence equivalent in substance to:

1. Parse the equations.
2. Identify the elimination variable `t`.
3. Isolate `t` from the first equation.
4. Substitute the isolated expression into the second equation.
5. Expand the resulting expression.
6. Simplify and rearrange.
7. Produce the derived relation.
8. Independently verify algebraic equivalence with the hidden target.
9. Where units are available, verify dimensional consistency.

The exact internal representation may differ, but the derivation must remain inspectable and reproducible.

## Acceptance criteria

A run is successful only when all applicable checks pass:

- **Algebraic correctness:** derived relation is equivalent to the hidden target.
- **Traceability:** intermediate transformation steps are retained.
- **No target leakage:** the target relation is not supplied to the derivation component.
- **Determinism:** identical inputs and configuration produce the same normalized result.
- **Independent verification:** correctness is checked separately from generation.
- **Failure visibility:** unsuccessful derivations are recorded with a structured failure reason rather than silently converted into a correct answer.

## Learning / transfer follow-up

Correctly solving Benchmark #01 is not, by itself, evidence of learning. Later experiments will separately test:

- **A — Learning:** repeated successful derivations can form a retained rule/strategy.
- **B — Transfer:** the retained strategy works on a structurally similar but unseen problem.
- **C — Context rejection:** the strategy is not applied when the structural conditions do not match.
- **D — Failure adaptation:** failed derivations reduce confidence or trigger repair rather than reinforcing the failed rule.

## Next implementation step

Implement the symbolic mathematics and derivation-trace components on a feature branch, add unit tests, then run Benchmark #01 before integrating the capability into the broader cognitive pipeline.

**Important:** this document records the benchmark specification and project checkpoint. It does not claim that the symbolic engine or Benchmark #01 has already been implemented or passed.
