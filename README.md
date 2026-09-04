# ANNE – Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-research%20preview-orange)](https://github.com/mgy421977-bit/anne)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--6591--0163-brightgreen)](https://orcid.org/0009-0002-6591-0163)

> **Intelligence is not only prediction.  
> Intelligence is the recursive organization of relationships.**

**ANNE (Adaptive Neural Nexus Engine)** is an open cognitive architecture research platform that explores whether **semantic validation**, **ethical decision constraints**, and **structured failure tracing (SFT)** can improve the reliability of existing foundation models through an additional cognitive orchestration layer.

It does **not** claim to be AGI, a new foundation model, or a solved hallucination system. It is a testable research hypothesis with a runnable v0.1 preview.

| | |
|--|--|
| **What exists** | Runnable six-stage pipeline, EthicCore, SQLite SFT memory, ANLA heuristic gate, open ablation micro-results |
| **What is hypothesized** | Gated validation improves measurable reliability vs pass-through generation |
| **Out of scope (for now)** | AGI claims, MatrAIx integration, production SOTA leaderboards |

---

## Quick Start

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"

python examples/basic_pipeline.py
python benchmarks/scripts/run_anla_ablation.py   # writes benchmarks/results/
pytest tests/unit -q
```

Latest micro-ablation summary: [`benchmarks/results/RESULTS.md`](benchmarks/results/RESULTS.md)

---

## Windows Agent

The repository includes a Tkinter desktop client under `desktop/anne_tinker.py`.

The Windows Tinker can use either:

- **OpenRouter Free** via `openrouter/free` (recommended for the free prototype)
- **Gemini** via the Gemini API

The reasoning provider is separated from ANNE's orchestration layer. ANNE owns the cognitive loop, tool execution and persistent memory; the model provider supplies language reasoning.

OpenRouter's `openrouter/free` router selects from currently available free models and filters for capabilities such as tool calling and structured output. Free-plan limits are subject to change; check OpenRouter's current pricing page before relying on the free tier for sustained workloads.

### Windows environment variables

```text
OPENROUTER_API_KEY
GITHUB_TOKEN
ANNE_REPOSITORY=mgy421977-bit/anne
ANNE_OPENROUTER_MODEL=openrouter/free
ANNE_PROVIDER=OpenRouter Free
```

Gemini remains available with:

```text
GEMINI_API_KEY
ANNE_GEMINI_MODEL=gemini-3.7-flash
ANNE_PROVIDER=Gemini
```

---

## Core Architecture

| # | Code (TR) | EN alias | Function |
|---|-----------|----------|----------|
| 1 | **DUY** | Perceive | Raw input reception — no prior judgment |
| 2 | **BAK** | Observe | Structural recognition + episodic memory query |
| 3 | **GÖR** | Recognize | Pattern matching + attention & priority |
| 4 | **ANLA** | Understand | **Semantic Validation Layer** + ethical synthesis |
| 5 | **HİSSET** | Evaluate | Empathic / contextual weighting |
| 6 | **YAP** | Act | Output only after prior stages clear |

Reject path records a **Structured Failure Trace (SFT)**. Score skeleton: [`docs/mathematics/anla_semantic_score.md`](docs/mathematics/anla_semantic_score.md).

### Ethical score (implemented)

```
total = (goodness × 0.4) + (equality × 0.4) − (harm × 0.2)
```

---

## Status (honest)

**Research Preview (v0.1.0)**

| Component | State |
|-----------|--------|
| Six-stage pipeline | Implemented |
| Fractal episodic memory (SQLite) + SFT | Implemented |
| ANLA heuristic + contradiction cap | Implemented |
| Ablation micro-results (n=30) | **Committed** — see `benchmarks/results/` |
| Gemini model provider | Implemented |
| OpenRouter free model provider | Implemented |
| GitHub read tools | Implemented |
| GitHub persistent learning memory | Implemented |
| Standard LLM benchmark superiority | **Not claimed** |
| Vector memory / multi-agent | Planned |

### v0.2 cognitive runtime

The agent runtime now includes an inspectable `CognitiveWorkspace`, a bounded
hierarchical planner, and a metacognitive review record. Model generation is
preceded and followed by the deterministic `DecisionLoop`; the model remains a
reasoning component rather than the authority that grants tool or action
permission. This is a step toward a cognitive architecture, not evidence of
AGI, consciousness, or safe autonomous deployment.

### v0.3 neuro-semantic core

The runtime now exposes semantic frames, traceable evidence and provenance,
an explicit belief store with conservative contradiction marking, plan-step
verification, and a neuro-symbolic reasoning audit. These components preserve
uncertainty instead of converting model output directly into fact. The current
grounding extractor is intentionally conservative and deterministic; it is a
stable contract for a future neural parser, not a claim of human-level semantic
understanding.

### v0.4 reliability and safety core

The agent now applies an allowlisted tool policy, redacts common credentials
before durable memory writes, supports evidence-weighted belief revision and
causal hypotheses, and can block plan steps whose preconditions are missing
while creating a repair step. These are conservative controls and do not make
the system safe for unsupervised high-stakes deployment.

Independent critiques: [`research/reviews/`](research/reviews/).  
MatrAIx note (external only): [`research/open_questions/matraix_and_hear.md`](research/open_questions/matraix_and_hear.md).

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

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

**Author:** Mustafa Gökhan Yılmaz (Kardo) · ORCID [0009-0002-6591-0163](https://orcid.org/0009-0002-6591-0163) · İzmir, Türkiye
