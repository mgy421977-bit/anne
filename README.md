# ANNE — Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-research%20preview-orange)](https://github.com/mgy421977-bit/anne)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--6591--0163-brightgreen)](https://orcid.org/0009-0002-6591-0163)

> **Intelligence is not only prediction. Intelligence is the recursive organization of relationships.**

**ANNE (Adaptive Neural Nexus Engine)** is a research platform for exploring cognitive orchestration around language models. The project separates perception, semantic/contextual processing, memory, verification, safety constraints, tool execution, and model generation rather than treating a foundation model as the sole authority.

ANNE is a **research system, not an AGI claim**. The repository deliberately distinguishes implemented engineering from experiments, hypotheses, and future research.

---

## What ANNE is trying to test

The central research question is:

> Can an additional cognitive orchestration layer improve the reliability, traceability, and controllability of model-assisted reasoning?

The project explores this through several interacting mechanisms:

- six-stage cognitive processing (`DUY → BAK → GÖR → ANLA → HİSSET → YAP`)
- semantic validation and contradiction handling
- persistent episodic/fractal memory
- structured failure traces (SFT)
- deterministic verification and safety gates
- neuro-symbolic reasoning components
- bounded planning and metacognitive review
- local/offline model providers
- bounded multi-agent collaboration
- reproducible benchmarks and ablation experiments

No component should be interpreted as proof of consciousness, general intelligence, or safe autonomous operation.

---

## Architecture at a glance

```text
                    ┌──────────────────────┐
                    │   Model Provider     │
                    │ local / API / LLM    │
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│                    ANNE Cognitive Runtime                 │
│                                                          │
│  DUY → BAK → GÖR → ANLA → HİSSET → YAP                  │
│   │      │      │      │        │        │               │
│   │      │      │      │        │        └─ action       │
│   │      │      │      │        └──────── contextual     │
│   │      │      │      └──────────────── semantic gate  │
│   │      │      └──────────────────── pattern/attention │
│   │      └────────────────────────── observation/memory │
│   └────────────────────────────────── perception         │
│                                                          │
│  Memory • Planning • Metacognition • Safety • Tools     │
│  Neuro-symbolic reasoning • Provenance • Verification   │
└──────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Traceable response   │
                    │ + evidence + state   │
                    └──────────────────────┘
```

### Cognitive stages

| Stage | Turkish | Role |
|---|---|---|
| 1 | **DUY** | Receive raw input without premature judgment |
| 2 | **BAK** | Observe structure and query relevant memory |
| 3 | **GÖR** | Recognize patterns, attention, and priority |
| 4 | **ANLA** | Semantic validation, contradiction handling, ethical synthesis |
| 5 | **HİSSET** | Contextual and evaluative weighting |
| 6 | **YAP** | Act or respond only after the preceding controls |

A reject path can be recorded as a **Structured Failure Trace (SFT)** instead of silently converting failure into an answer.

---

## Current repository structure

```text
anne/
├── src/anne/
│   ├── agent/              Agent and offline runtime
│   ├── api/                API surface
│   ├── core/               Cognitive core, learning, verification, planning
│   ├── dream/              Dream-cycle research components
│   ├── memory/             Persistent/fractal memory
│   ├── multi_agent/        Bounded specialist coordination
│   ├── mythos/              Proposal/generative research layer
│   ├── neuro_symbolic/     Neuro-symbolic reasoning components
│   ├── providers/          Model-provider adapters
│   ├── safety/             Tool/action safety controls
│   ├── semantics/          Semantic frames and grounding
│   ├── tools/              Tool execution and integration
│   └── world/              World/context representations
│
├── benchmarks/             Ablations, benchmark runners and results
├── datasets/               Versioned benchmark datasets/prompts
├── desktop/                Windows/Tkinter clients and build scripts
├── docs/                   Architecture, mathematics and research notes
├── research/               Reviews, decision logs and open questions
├── applications/           Experimental application entry points
├── tests/                  Unit/integration tests
├── ROADMAP.md              Research/engineering roadmap
├── CHANGELOG.md            Change history
└── pyproject.toml          Package and development configuration
```

The repository is intentionally organized so that **implementation, evidence, and speculation remain distinguishable**.

---

## Quick start

Requirements: Python 3.12+.

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
python -m pip install -e ".[dev]"

# Example pipeline
python examples/basic_pipeline.py

# Test suite
pytest tests/unit -q
```

For the benchmark suite:

```bash
python benchmarks/scripts/run_anla_ablation.py
```

Published benchmark artifacts live under `benchmarks/results/`.

---

## Local / offline runtime

ANNE includes a local execution path designed to reduce dependence on external APIs. The offline runtime can use a local model backend such as Ollama or another OpenAI-compatible local endpoint, while persistence remains local.

Example:

```python
from anne.agent.offline import create_offline_agent

agent = create_offline_agent(
    model="qwen2.5:7b",
    db_path="anne_offline.db",
)

result = agent.run("Summarize the local workspace safely.")
print(result.response)
```

Local execution does **not** mean that the system is autonomous or safe for unsupervised high-stakes use.

---

## Model providers

ANNE is designed so that the reasoning provider is replaceable. Depending on the installed configuration, the repository can work with hosted providers or local model endpoints.

The architectural principle is:

```text
Model = reasoning component
ANNE = orchestration + memory + verification + policy
```

The model output is therefore not treated as an unconditional authority for tool use or external action.

---

## Reliability and safety layer

The current architecture includes conservative controls such as:

- allowlisted tool policies
- credential redaction before durable memory writes
- evidence-weighted belief revision
- contradiction marking
- provenance/evidence tracking
- plan-step verification
- missing-precondition detection and repair steps
- bounded planning and deliberation
- deterministic decision/verification paths

These mechanisms are engineering controls, **not a safety certification**.

---

## Memory and learning

ANNE contains persistent memory and learning-oriented components, but the project follows an important evidence rule:

> A correct answer is not, by itself, evidence that ANNE learned.

Learning claims must be demonstrated separately through reproducible experiments covering, where applicable:

1. repeated experience,
2. rule formation or update,
3. transfer to a related new problem,
4. contextual rejection when a learned rule does not apply,
5. confidence or rule weakening after an incorrect outcome.

Benchmark results are stored separately from architectural claims so that implementation status is not confused with experimental proof.

---

## Mathematics, physics and symbolic reasoning

ANNE's research direction includes deterministic symbolic reasoning, derivation tracing, dimensional/unit validation, and physics-oriented computation. These components are treated as **verification and reasoning infrastructure**, not as evidence of general intelligence.

Where a derivation benchmark is used, the project distinguishes:

- numerical calculation,
- symbolic manipulation,
- derivation trace,
- independent verification,
- dimensional consistency,
- and actual learning/transfer.

A mathematically correct derivation demonstrates the corresponding computational capability; it does not automatically demonstrate learning or understanding.

---

## Benchmarks and evidence

The repository contains:

- ANLA ablation experiments
- benchmark datasets/prompts
- reproducible runner scripts
- committed result artifacts
- research reviews and decision records

See:

- [`benchmarks/`](benchmarks/)
- [`benchmarks/results/`](benchmarks/results/)
- [`ROADMAP.md`](ROADMAP.md)
- [`research/`](research/)

**Evidence first:** claims should be promoted from hypothesis to implemented result only when the corresponding code, test, or benchmark artifact exists.

---

## Project status

**Research Preview / Alpha — active development**

| Area | Current position |
|---|---|
| Six-stage cognitive pipeline | Implemented |
| Persistent/fractal memory + SFT | Implemented |
| Semantic validation / contradiction controls | Implemented in research architecture |
| Cognitive workspace / planning / metacognition | Implemented in research architecture |
| Neuro-symbolic components | Implemented / experimental |
| Safety and verification controls | Implemented / conservative |
| Local/offline runtime | Implemented |
| Model-provider abstraction | Implemented |
| Multi-agent coordinator | Experimental / bounded |
| Benchmark and ablation infrastructure | Implemented |
| General intelligence / AGI | **Not claimed** |
| Human-level understanding | **Not claimed** |
| Unsupervised high-stakes deployment | **Not supported** |

For the authoritative milestone sequence, see [`ROADMAP.md`](ROADMAP.md).

---

## Research discipline

ANNE uses four practical labels when discussing new capabilities:

- **IMPLEMENTED** — present in the repository and testable.
- **EXPERIMENTAL** — implemented for controlled evaluation; not established as generally reliable.
- **HYPOTHESIS** — a research proposition requiring evidence.
- **ROADMAP** — planned work that should not be described as current capability.

This distinction is a core part of the project, not just documentation style.

---

## Development

Install development dependencies with:

```bash
python -m pip install -e ".[dev]"
```

Recommended checks before a change is considered complete:

```bash
ruff check .
mypy src
pytest -q
```

Keep benchmark outputs and research notes reproducible. Avoid committing credentials, local databases, generated binaries, or machine-specific artifacts.

---

## Roadmap

The roadmap prioritizes evidence before expansion:

1. strengthen benchmark coverage and measurement;
2. validate semantic gates and failure paths;
3. test learning/transfer independently from calculation correctness;
4. improve local runtime and persistent memory;
5. evaluate symbolic/physical reasoning with reproducible traces;
6. document limitations and publish evidence before making broader claims.

See [`ROADMAP.md`](ROADMAP.md) for milestone-level criteria.

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

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

**Author:** Mustafa Gökhan Yılmaz · ORCID [0009-0002-6591-0163](https://orcid.org/0009-0002-6591-0163) · İzmir, Türkiye
