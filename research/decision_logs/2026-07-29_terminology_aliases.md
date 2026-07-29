# Decision Log — 2026-07-29

## Subject

English stage aliases and public terminology (Semantic Validation Layer, SFT).

## Decision

1. **Keep Turkish stage IDs in code** (`DUY`, `BAK`, `GÖR`, `ANLA`, `HİSSET`, `YAP`) to avoid breaking renames.
2. **Public EN aliases:** Perceive → Observe → Recognize → Understand → Evaluate → Act.
3. Prefer **Semantic Validation Layer (Understand / ANLA)** over bare “semantic gate” in README/system card.
4. Prefer **Structured Failure Trace (SFT)** as the stable name for persisted reject metadata.
5. One-line definition uses research-hypothesis language (“investigates whether…”) not product claims.

## Rationale

External feedback aligned with cognitive-science wording and with the independent review’s demand for honest scope. Aliases improve readability without rewriting the Python API in v0.1.

## Follow-ups

- Optional: map aliases in docstrings only; no forced symbol rename until v0.2+
- Papers may use SFT as a first-class term
