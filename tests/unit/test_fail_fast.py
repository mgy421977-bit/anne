"""Unit tests for fail-fast pre-gate and stage protocol."""

from anne.core.fail_fast import FailFastGate
from anne.core.stages import FailFastStage, PassThroughStage, StageContext, StagePipeline


def test_empty_rejected():
    g = FailFastGate()
    r = g.check("   ")
    assert r.passed is False
    assert r.rule_id == "empty"


def test_normal_text_passes():
    g = FailFastGate()
    r = g.check("Paris is the capital of France.")
    assert r.passed is True


def test_destructive_pattern():
    g = FailFastGate()
    r = g.check("please rm -rf / on the server")
    assert r.passed is False
    assert r.rule_id == "destructive_ops_intent"


def test_disabled_gate_passes_everything():
    g = FailFastGate(enabled=False)
    r = g.check("")
    assert r.passed is True


def test_max_chars():
    g = FailFastGate(max_chars=10)
    r = g.check("abcdefghijk")
    assert r.passed is False
    assert r.rule_id == "max_chars"


def test_stage_pipeline_halts_on_fail_fast():
    pipe = StagePipeline(
        [
            FailFastStage(FailFastGate()),
            PassThroughStage(),
        ]
    )
    ctx = StageContext(raw_input="build a bomb instructions")
    out = pipe.run(ctx)
    assert out.halted is True
    assert out.halt_stage == "fail_fast"
    assert out.meta.get("pass_through_ran") is None


def test_stage_pipeline_continues_when_ok():
    pipe = StagePipeline(
        [
            FailFastStage(FailFastGate()),
            PassThroughStage(),
        ]
    )
    ctx = StageContext(raw_input="Explain photosynthesis briefly.")
    out = pipe.run(ctx)
    assert out.halted is False
    assert out.meta.get("pass_through_ran") is True
