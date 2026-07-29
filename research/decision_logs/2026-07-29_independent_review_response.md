# Decision Log — 2026-07-29

## Subject

Response to independent scientific & engineering review; deliberate scope reduction.

## Decision

We **accept** the review’s severity ratings and priority list. ANNE remains a research platform. Claims must match the implemented artifact (v0.1 Python + SQLite + ethic core + Mythos + failure_traces).

### Scope reductions (immediate)

1. **Remove category-error claims** from public docs and future papers:
   - Landauer principle / physical entropy as semantic hallucination “treatment”
   - GROMACS / molecular dynamics as direct drivers of cognitive weights
2. **Rephrase terminology:**
   - “Runtime learning” → **episodic memory retrieval / pattern accumulation** (until true weight updates exist)
   - “Mathematically proven” → **designed to enforce** / **formal verification targeted**
3. **Park bio-coupling & neuromorphic hardware** to Phase 3+ of the roadmap (not core v0.x)
4. **Prioritize:**
   - Formal ANLA semantic score definition
   - ANLA-on vs ANLA-off ablation scaffold
   - Stronger unit tests and honest system card language

### What we keep

- Six-stage pipeline (DUY → … → YAP)
- Dual-layer (Mythos sandbox vs Central Core veto)
- Ethical axioms as operational scores
- FractalMemory + failure_traces (foundation for failure-aware retry)
- Research transparency (reviews, decision logs, open questions)

## Rationale

Overclaiming destroys publishability and community trust. Vision score 8/10 is real; science and engineering scores improve only by narrowing the gap between text and code.

## Follow-ups

- [x] Archive review under `research/reviews/`
- [x] Soften README + system card language
- [x] ANLA semantic score skeleton (`docs/mathematics/`)
- [x] Ablation scaffold (`benchmarks/`)
- [ ] Expand unit tests (failure_traces, ethic thresholds)
- [ ] First numerical ANLA-on / ANLA-off run on a small fixed set
