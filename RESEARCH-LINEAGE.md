# ANNE Research Lineage

## Status: Frozen Legacy Line

`anne` is the **first/main ANNE development line** and is now frozen as a historical research snapshot.

Active architectural development has moved to the newer `anne-ai` research platform, with reusable foundational capabilities being developed in `anne-core`.

### Current development direction

```text
anne
  → first/main ANNE line
  → FROZEN / historical reference

anne-ai
  → current ANNE research platform
  → active architectural development

anne-core
  → first foundational/core engine layer of the current direction
  → reusable, installable core capabilities
```

### Relationship between the three repositories

The three repositories are **one ANNE research lineage with three distinct roles**, not three unrelated versions or products.

1. **`anne`** is the original first/main development line. It is frozen so the original architecture and research history remain available for reference and reproducibility.
2. **`anne-ai`** is the current canonical research platform. New architecture, integration work, experiments, and research milestones are developed here.
3. **`anne-core`** is the first foundational/core engine layer of the current direction. Reusable capabilities that can be isolated, tested, and installed independently are developed here alongside `anne-ai`.

The practical relationship is therefore:

```text
Original ANNE research line
        │
        ▼
     anne
   FROZEN
        │
        │ architectural continuation
        ▼
   anne-ai  ◄──────────────►  anne-core
 CURRENT PLATFORM            FOUNDATIONAL CORE
 active research             reusable core layer
```

`anne-ai` and `anne-core` are developed together but are not interchangeable: `anne-ai` is the broader research and integration surface, while `anne-core` contains the foundational capabilities that are suitable for independent reuse.

### Vitavolt Research connection

ANNE belongs to the **Vitavolt Research** network. The public research hub is:

- **Vitavolt Research:** https://vitavoltglobal.com/research/
- **ANNE canonical page:** https://vitavoltglobal.com/anne.html
- **ANNE research overview:** https://vitavoltglobal.com/research/anne-ai.html
- **ANNE architecture:** https://vitavoltglobal.com/research/anne-architecture.html
- **Research publications:** https://vitavoltglobal.com/research/publications.html

The Vitavolt website acts as the public research/entity layer, while GitHub provides the corresponding source and research repository layer.

The freeze does not invalidate the historical work in this repository. It preserves the original ANNE line for reproducibility, reference, and research history.

New architecture, experiments, integrations, and research milestones should be associated with `anne-ai`; foundational capabilities appropriate for extraction belong in `anne-core`.

This repository is not presented as the current implementation of ANNE and makes no AGI achievement claim.

## Research Network

- Legacy / first line: https://github.com/mgy421977-bit/anne
- Current canonical platform: https://github.com/mgy421977-bit/anne-ai
- Foundational core: https://github.com/mgy421977-bit/anne-core
- Vitavolt Research: https://vitavoltglobal.com/research/
