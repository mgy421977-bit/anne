# ANNE v0.1.0 — Research Preview

**Tag:** `v0.1.0-research-preview`  
**Date:** 2026-07-29

## Summary

First public research snapshot of **ANNE** (Adaptive Neural Nexus Engine): a six-stage cognitive pipeline with an operational ethical core and persistent episodic memory, including structured **failure traces** for semantic reject paths.

This is **not** a production AGI system and **not** a claim that hallucination is solved.

## Install

```bash
git clone https://github.com/mgy421977-bit/anne.git
cd anne
pip install -e ".[dev]"
python examples/basic_pipeline.py
python -m pytest tests/unit -q
python benchmarks/scripts/run_anla_ablation.py
```

## Highlights

- Dual layer: Mythos (hypothesis generation) vs Central Core (ethical veto)
- UNDERSTAND (ANLA) path can record failure traces on reject
- Honest system card and independent-review response under `research/`

## Next (roadmap, not promises)

- Expand ablation fixture and publish raw ON/OFF counts
- Stronger semantic proxies for ANLA score
- Broader integration tests

## Cite

See `CITATION.cff` and README bibtex entry.
