# ANNE-MYTHOS Dual Engine System — Technical System Card

**Version:** 2.1  
**Date:** July 2026  
**Developer:** Mustafa Gökhan Yılmaz (Kardo)  
**License:** Apache-2.0  
**Status:** Research preview (v0.1 implementation)

-----

## 1. Summary

ANNE-MYTHOS combines two complementary components in one experimental cognitive framework.

**MYTHOS** is a curiosity and hypothesis-generation loop: it takes a topic, produces iterative hypotheses, and updates confidence (placeholder or Anthropic API).

**ANNE** (Adaptive Neural Nexus Engine) is a six-stage pipeline with an operational ethical score and persistent episodic memory. Every decision is intended to pass through semantic and ethical gates before output.

**Core proposition:**

> *Intelligence is not only prediction. Intelligence is the recursive organization of relationships.*

This card describes what is **implemented today**, not the long-horizon NuN Nexus vision.

-----

## 2. Operational Axioms

These are concrete terms in the decision score, not soft slogans.

1. **Goodness (0 → 1)** — Existence is recognized; no consciousness is zeroed.
2. **Equality (1 == 1)** — No hierarchy of weight among existing consciousnesses.
3. **Minimum harm** — Explicit harm term in the score.
4. **Universal benefit** — Prefer outcomes that raise aggregate benefit.
5. **Low-probability preservation** — Hypotheses with P → 0 are not deleted.
6. **Conflict → separate solutions** — In conflict, the system does not take sides.

Decision score (implemented):

```
total = (goodness × 0.4) + (equality × 0.4) − (harm × 0.2)
```

- total ≥ 0.70 → ONAYLA  
- total ≥ 0.40 → AYRI_ÇÖZÜM  
- total < 0.40 → REDDET  

-----

## 3. Architecture (v0.1)

| Stage | Role |
|-------|------|
| **DUY** | Raw input reception |
| **BAK** | Structure + episodic memory query |
| **GÖR** | Attention / priority |
| **ANLA** | Semantic validation gate + ethical synthesis (score skeleton; see math docs) |
| **HİSSET** | Empathic weighting across listed consciousnesses |
| **YAP** | Output only if gates clear |

**Memory:** FractalMemory (SQLite) stores hypotheses, decisions, patterns, learned rules, empathy links, and **failure traces**. This is **episodic retrieval and pattern accumulation**, not weight-level online learning.

**Dual layer:** Mythos (unconstrained hypothesis generation) vs Central Core (ethical veto).

-----

## 4. Safety & alignment (implemented constraints)

- No consciousness zeroed in the scoring model
- Low-probability hypotheses retained in memory
- Conflict path prefers separate solutions
- Decisions and REDDET paths can be audited via SQLite + failure_traces
- Mythos does not execute actions; it only proposes hypotheses

-----

## 5. Explicit non-claims (v0.1)

- No claim of zero hallucination in production LLM settings
- No thermodynamic / Landauer treatment of semantic error
- No GROMACS or molecular dynamics coupling in the running code
- No formal proof of ANLA optimality yet — see `docs/mathematics/anla_semantic_score.md`
- Neuromorphic / BCI targets are roadmap items, not current deliverables

-----

## 6. Roadmap (honest)

- **v0.1** (current): Six stages + SQLite memory + Mythos + failure_traces
- **v0.2**: ANLA semantic score heuristics + ANLA on/off ablation numbers
- **v0.3**: Stronger retrieval (embeddings) + broader unit tests
- **v0.4**: Multi-agent experiments
- **Later:** Formal verification targets, optional vector backends, long-horizon hardware notes

-----

## 7. Citation

Mustafa Gökhan Yılmaz, ORCID: 0009-0002-6591-0163  
İzmir, Türkiye

Related: ATHENA (Zenodo DOI: 10.5281/zenodo.20562973)
