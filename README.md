# ANNE – Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-research%20preview-orange)](https://github.com/mgy421977-bit/anne)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--6591--0163-brightgreen)](https://orcid.org/0009-0002-6591-0163)

> **Intelligence is not only prediction.  
> Intelligence is the recursive organization of relationships.**

ANNE is an open **research platform** exploring a six-stage cognitive architecture aimed at two limitations of current large language models:

1. No real-time **semantic validation loop** during inference (a major driver of cascading hallucination).
2. No structurally embedded, **human-first ethical core** before output generation.

This repository ships a **v0.1 research preview**: a working pipeline, ethical score, SQLite episodic memory (including failure traces), and a Mythos curiosity loop. Long-horizon ideas (neuromorphic routing, formal VSA bridges, bio-coupling) belong in the roadmap — not in claims about the current binary.

---

## Core Architecture

Every input is processed through a mandatory six-stage pipeline:

| Stage | Name (TR) | Function |
|-------|-----------|----------|
| 1 | **DUY** (Hear) | Raw input reception – no prior judgment |
| 2 | **BAK** (Look) | Structural recognition + episodic memory query |
| 3 | **GÖR** (See) | Pattern matching + attention & priority selection |
| 4 | **ANLA** (Understand) | **Semantic validation gate** + ethical synthesis |
| 5 | **HİSSET** (Feel) | Empathic simulation across affected consciousnesses |
| 6 | **YAP** (Do) | Output generation (only after gates clear) |

If **ANLA** fails validation, the system records a **failure trace** and is designed to return toward **DUY** with that meta-tag — failure-aware retry rather than blind regeneration. The formal score for ANLA is specified as a research skeleton in [`docs/mathematics/anla_semantic_score.md`](docs/mathematics/anla_semantic_score.md).

### Dual-Layer Processing

- **Subconscious (Mythos):** Unconstrained curiosity & hypothesis generation
- **Central Core (ANNE):** Ethical evaluation + veto authority

### Ethical Axioms (Operational)

Applied as terms in the decision score (not slogans):

1. **Goodness (0 → 1)** — Existence recognized; no consciousness zeroed
2. **Equality (1 == 1)** — No hierarchy of weight among existing consciousnesses
3. **Minimum Harm** — Explicit harm term
4. **Universal Benefit** — Prefer higher aggregate benefit
5. **Low-Probability Preservation** — Hypotheses with P → 0 are kept
6. **Conflict → Separate Solutions** — System does not take sides

```
total = (goodness × 0.4) + (equality × 0.4) − (harm × 0.2)
```

---

## Quick Start

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"

# Optional: Anthropic API for real hypothesis generation
export ANTHROPIC_API_KEY="sk-ant-..."

python examples/basic_pipeline.py
```

---

## Repository Structure

```
anne/
├── src/anne/               # Core library (pipeline, ethic core, memory, mythos)
├── applications/           # Independent apps on the same core
├── examples/
├── benchmarks/             # Ablation scaffolds & evaluation protocols
├── datasets/
├── docs/                   # Architecture, mathematics, system card
├── papers/
├── design/
├── research/               # Decision logs, open questions, independent reviews
├── governance/
└── tests/
```

---

## Status (honest)

**Research Preview (v0.1.0)**

| Component | State |
|-----------|--------|
| Six-stage pipeline | Implemented |
| Fractal episodic memory (SQLite) | Implemented |
| Failure traces (ANLA retry support) | Implemented |
| Mythos curiosity loop | Implemented (placeholder + Anthropic API) |
| Dream cycle | Implemented |
| ANLA formal semantic score | Skeleton only |
| ANLA on/off ablation numbers | Scaffold only |
| Vector memory / multi-agent | Planned |

Episodic memory is **retrieval + pattern accumulation**, not weight-level online learning.

Independent critique archive: [`research/reviews/`](research/reviews/).

---

## Citation

```bibtex
@software{yilmaz2026anne,
  author       = {Yılmaz, Mustafa Gökhan},
  title        = {ANNE – Adaptive Neural Nexus Engine},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/mgy421977-bit/anne},
  orcid        = {0009-0002-6591-0163}
}
```

Or use `CITATION.cff`.

---

## Related Work

- **ATHENA** (Scalar–Tensor Emergent Information Gravity) — theoretical physics framework by the same author
- Constitutional AI (Anthropic, 2022)
- Reward Modeling (Stiennon et al., 2020)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).  
Research questions, architectural critiques, and experimental results are especially welcome.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

**Author**  
Mustafa Gökhan Yılmaz (Kardo)  
ORCID: [0009-0002-6591-0163](https://orcid.org/0009-0002-6591-0163)  
İzmir, Türkiye
