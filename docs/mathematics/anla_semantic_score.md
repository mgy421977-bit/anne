# ANLA Semantic Score — Formal Skeleton (v0.1)

**Status:** Research draft — not a completed proof  
**Goal:** Give ANLA a concrete, testable scoring function so the gate is more than a named stage.

---

## Problem

ANLA must decide whether a candidate output is **semantically coherent** with the input context and prior failure traces before the ethical score is applied. Without a defined function, the gate is procedural theater.

## Target form

We seek a score $S_{\mathrm{ANLA}} \in [0, 1]$:

$$
S_{\mathrm{ANLA}} = \alpha \, C_{\mathrm{ctx}} + \beta \, C_{\mathrm{log}} + \gamma \, C_{\mathrm{trace}}
$$

with $\alpha + \beta + \gamma = 1$, $\alpha,\beta,\gamma \ge 0$.

| Term | Meaning (v0.1 intent) |
|------|------------------------|
| $C_{\mathrm{ctx}}$ | Context consistency — overlap / entailment between candidate and DUY input |
| $C_{\mathrm{log}}$ | Logical coherence — internal contradiction check (lightweight rules or NLI proxy) |
| $C_{\mathrm{trace}}$ | Failure-trace awareness — penalty if candidate repeats a recent failure meta-tag |

**Gate rule (draft):**

- $S_{\mathrm{ANLA}} \ge \tau$ → pass to HİSSET / ethical score  
- $S_{\mathrm{ANLA}} < \tau$ → write `failure_trace`, return to DUY with meta-tag  

Default research threshold: $\tau = 0.5$ (tunable; must be ablated).

## What is deliberately NOT claimed

- No claim that $S_{\mathrm{ANLA}}$ is information-theoretically optimal
- No Landauer / thermodynamic interpretation
- No requirement for continuous SNN / VSA until a separate formal note exists

## Implementation path (engineering)

1. **v0.1 (now):** Heuristic $C_{\mathrm{ctx}}$ via token/lemma overlap; $C_{\mathrm{trace}}$ via `get_recent_failures()`; $C_{\mathrm{log}}$ stub = 1.0
2. **v0.2:** Replace overlap with embedding cosine or NLI model; log contradictions
3. **v0.3:** Bayesian confidence update of $\tau$ from ablation outcomes

## Required experiments

- Ablation: ANLA on vs off on a fixed prompt set (see `benchmarks/ablation_anla.md`)
- Sensitivity of $\tau$ vs false-block / false-pass rates

## Open questions

- Formal bound on retry loops (infinite veto risk)
- Calibration of $(\alpha,\beta,\gamma)$ without overfitting to toy data
