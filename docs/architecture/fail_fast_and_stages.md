# Fail-fast and Stage protocol

## Fail-fast

`anne.core.fail_fast.FailFastGate` applies deterministic checks **before** ANLA:

- empty input
- max length
- small explicit rule list (EN/TR patterns) for high-risk intents

Rejects write SFT with `stage=FAIL_FAST` when using `AnnePipeline.run_with_fail_fast`.

This is **not** a full safety product. Rules are transparent and intentionally narrow.

## Stage protocol

```python
from anne.core.stages import Stage, StageContext, StagePipeline, FailFastStage, PassThroughStage
from anne.core.fail_fast import FailFastGate

pipe = StagePipeline([
    FailFastStage(FailFastGate()),
    PassThroughStage(),  # stand-in for custom ANLA / ethic stages
])
ctx = StageContext(raw_input="...")
result = pipe.run(ctx)
```

Legacy `AnnePipeline` stage methods remain the primary runtime; Stage ABC is the extension surface for ablations.
