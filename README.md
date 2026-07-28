# ANNE – Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-research%20preview-orange)](https://github.com/mgy421977-bit/anne)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--6591--0163-brightgreen)](https://orcid.org/0009-0002-6591-0163)

> **Intelligence is not only prediction.  
> Intelligence is the recursive organization of relationships.**

ANNE is an open research platform exploring a **six-stage cognitive architecture** designed to address two fundamental limitations of current large language models:

1. The absence of a real-time **semantic validation loop** during inference (the primary mechanism of hallucination).
2. The lack of a structurally embedded, **human-first ethical core** that operates before output generation.

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
| 6 | **YAP** (Do) | Output generation (only after all gates clear) |

If **ANLA** fails semantic validation, the system returns to **DUY** carrying a failure trace — enabling failure-aware retry rather than blind regeneration.

### Dual-Layer Processing

- **Subconscious (Mythos)**: Unconstrained curiosity & hypothesis generation
- **Central Core (ANNE)**: Ethical evaluation + veto authority

### Ethical Axioms (Operational)

These are not soft guidelines. They are mathematical operations applied at every decision node:

1. **Goodness (0 → 1)**: Existence is recognized. No consciousness may be zeroed.
2. **Equality (1 == 1)**: No hierarchy of weight among existing consciousnesses.
3. **Minimum Harm**: Explicit harm minimization term in the decision score.
4. **Universal Benefit**: Maximize aggregate benefit across all affected parties.
5. **Low-Probability Preservation**: Hypotheses with P → 0 are never discarded.
6. **Conflict → Separate Solutions**: In conflict, the system does not take sides.

Decision score:

```
total = (goodness × 0.4) + (equality × 0.4) − (harm × 0.2)
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/mgy421977-bit/anne.git
cd anne

# Install (editable)
pip install -e ".[dev]"

# Optional: Anthropic API for real hypothesis generation
export ANTHROPIC_API_KEY="sk-ant-..."

# Run basic example
python examples/basic_pipeline.py
```

---

## Repository Structure

```
anne/
├── src/anne/               # Core library (pipeline, ethic core, memory, mythos)
├── applications/           # Independent applications built on the core
│   ├── simulation_feedback/
│   └── mother_ai/
├── examples/               # Runnable demonstrations
├── benchmarks/             # Hallucination & ethical decision benchmarks
├── datasets/               # Future evaluation datasets
├── docs/                   # Architecture, algorithms, mathematics, tutorials
├── papers/                 # White papers, preprints, conference materials
├── design/                 # Diagrams (Mermaid, SVG, Draw.io)
├── research/               # Literature, decision logs, open questions
├── governance/             # Vision, Mission, Research Charter
└── tests/
```

---

## Status

**Research Preview (v0.1.0)**

- Six-stage pipeline — implemented
- Fractal episodic memory (SQLite) — implemented
- Mythos curiosity loop — implemented (placeholder + Anthropic API)
- Dream cycle (offline pattern synthesis) — implemented
- Formal hallucination benchmarks — planned
- Vector memory backend — planned
- Multi-agent coordination — planned

---

## Citation

If you use ANNE in academic work, please cite:

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

Or use the `CITATION.cff` file.

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
