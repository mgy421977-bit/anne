# DecisionLoop

Single preferred entry point for gated decisions.

```text
input → FailFast → DUY → BAK → GÖR → ANLA → HİSSET → YAP → DecisionResult
```

## Usage

```python
from anne.core.decision_loop import DecisionLoop
from anne.core.cognitive_state import Consciousness

loop = DecisionLoop()
result = loop.run(
    raw_input="Two teams conflict over budget; propose process options.",
    parties=[Consciousness(id="team_a"), Consciousness(id="team_b")],
)
print(result.status, result.verdict, result.action)
print(result.as_dict())
```

## Guarantees (honest)

- Callers using `DecisionLoop.run` do not skip FailFast or the reference pipeline stages.
- Rejects can originate from FailFast, ANLA, or EthicCore.
- SFT is written on FailFast and ANLA failures via the pipeline/memory layer.

## Non-guarantees

- Not consciousness, not unhackable, not production safety certification.
- Heuristic gates only; see `governance/CORE_RULES.md`.
