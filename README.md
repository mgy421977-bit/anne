# ANNE – Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-research%20preview-orange.svg)](https://github.com/mgy421977-bit/anne)

> **Intelligence is not only prediction.  
> Intelligence is the recursive organization of relationships.**

**ANNE (Adaptive Neural Nexus Engine)** is an open cognitive architecture research platform that explores whether semantic validation, ethical decision constraints, structured failure tracing (SFT), and explicit hypothesis handling can improve the reliability of existing foundation models through an additional cognitive orchestration layer.

It does **not** claim to be AGI, a new foundation model, or a solved hallucination system. It is a testable research hypothesis with a runnable preview.

## Core Architecture

ANNE uses the six-stage discipline:

1. **DUY** — Perceive
2. **BAK** — Observe
3. **GÖR** — Recognize
4. **ANLA** — Understand
5. **HİSSET** — Evaluate
6. **YAP** — Act

The current GÖR implementation evaluates multiple hypothesis candidates, tracks their ranking and uncertainty, and preserves meaningful low-probability alternatives for later validation.

## Windows Agent

The repository includes a Tkinter desktop client under `desktop/anne_tinker.py`.

The Windows Tinker can use either OpenRouter or Gemini as its reasoning provider while ANNE controls orchestration, tools, and persistent GitHub memory.

ANNE also includes a **guarded self-improvement engine** under `src/anne/agent/self_improvement.py` and an agent integration under `src/anne/agent/self_improving_runtime.py`.

The self-improvement workflow is deliberately constrained:

```text
problem / request
      ↓
analysis + hypotheses
      ↓
explicit change plan
      ↓
anne/improve-* feature branch
      ↓
create / update / delete files
      ↓
CI validation
      ↓
Pull Request → human review
```

`main` and `master` remain protected from ANNE write tools. Existing-file mutations use the current Git blob SHA, and ANNE never merges its own pull requests.

## Status (honest)

**Research Preview**

| Component | State |
|-----------|-------|
| Six-stage cognitive pipeline | Implemented |
| Fractal episodic memory + SFT | Implemented |
| ANLA heuristic + contradiction cap | Implemented |
| Multi-hypothesis SEE/GÖR | Implemented |
| Hypothesis Engine | Implemented |
| Gemini model provider | Implemented |
| OpenRouter free model provider | Implemented |
| GitHub read tools | Implemented |
| GitHub write/change tools | Implemented — guarded feature branches |
| Self-improvement engine | Implemented — PR/human-review gate |
| Autonomous merge to main | Not permitted |
| Standard LLM benchmark superiority | Not claimed |
| Vector memory / multi-agent | Planned |

## Quick Start

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"

python examples/basic_pipeline.py
pytest tests/unit -q
```

## Citation

```bibtex
@software{yilmaz2026anne,
  author       = {Yılmaz, Mustafa Gökhan},
  title        = {ANNE – Adaptive Neural Nexus Engine},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/mgy421977-bit/anne}
}
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).

**Author:** Mustafa Gökhan Yılmaz · ORCID 0009-0002-6591-0163 · İzmir, Türkiye
