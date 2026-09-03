# ANNE – Adaptive Neural Nexus Engine

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> **Intelligence is not only prediction. Intelligence is the recursive organization of relationships.**

ANNE is an experimental cognitive architecture research platform. It explores whether a structured six-stage pipeline, semantic validation, ethical constraints, failure tracing, explicit hypothesis handling, and optional model assistance can improve reasoning reliability.

ANNE does **not** claim AGI, consciousness, or unsupported benchmark superiority.

## Core architecture

`DUY → BAK → GÖR → ANLA → HİSSET → YAP`

The deterministic pipeline is the primary execution path. It can generate and rank multiple hypotheses locally, track novelty and uncertainty, preserve alternatives, and complete the cognitive stages without calling an LLM.

LLMs are optional adapters for language synthesis, research, complex external-tool tasks, or other cases where model assistance is useful.

## Pipeline-first API

```python
from anne import Consciousness, run_pipeline

state = run_pipeline(
    "Yeni bir hipotezi güvenlik ve tutarlılık açısından değerlendir.",
    [Consciousness(id="C1")],
)

print(state.output)
print(state.uncertainty)
print(state.hypothesis_rankings)
```

`hypothesis=None` is now a supported path through `AnnePipeline`; the local `HypothesisEngine` creates the candidate set.

## Windows Tinker

`desktop/anne_tinker.py` provides two explicit modes:

- **Pipeline First** — deterministic ANNE pipeline; LLM optional.
- **Agent / Tools** — model-backed tool execution for repository and external tasks.

The Tinker can attach research material before sending a request. Supported inputs include text/Markdown, source code and structured text files, DOCX, and PDF. Attachments are treated as evidence and the prompt explicitly asks ANNE to distinguish claims, inference, contradiction, and uncertainty.

Pipeline First can optionally pass its result and source material to Gemini for a second analysis pass looking for hidden assumptions, contradictions, or alternative interpretations that the deterministic layer may miss.

The default Gemini model is `gemini-3.7-flash`. OpenRouter remains available as an alternative provider.

## Memory and safety

FractalMemory remains a local SQLite memory layer containing hypotheses, decisions, learned rules, empathy relations, and structured failure traces. Repository mutation is not part of the deterministic pipeline path.

When Agent / Tools mode is used, repository operations remain subject to the existing GitHub safety controls and review workflow. ANNE should never treat memory or model output as unquestionable truth.

## Status

**Research Preview**

| Component | State |
|---|---|
| Six-stage cognitive pipeline | Implemented |
| Local deterministic HypothesisEngine | Implemented |
| Multi-hypothesis ranking + uncertainty | Implemented |
| `anne.run_pipeline(...)` | Implemented |
| Gemini provider | Implemented |
| OpenRouter provider | Implemented |
| Windows Tinker Pipeline First mode | Implemented |
| Tinker research-file attachments | Implemented |
| GitHub read tools | Implemented |
| GitHub guarded write/self-improvement branch | Experimental / separate PR |
| GitHub persistent JSONL memory sync | Planned |
| Vector memory / multi-agent | Planned |

## Development

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"
pytest tests/unit -q
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).

**Author:** Mustafa Gökhan Yılmaz · ORCID 0009-0002-6591-0163 · İzmir, Türkiye
