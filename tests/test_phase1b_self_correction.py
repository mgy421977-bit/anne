from anne.core.self_correction import FailureClass, SelfCorrectionPlanner


def test_failure_taxonomy_maps_sft_tags():
    planner = SelfCorrectionPlanner()
    assert planner.classify("semantic_reject") is FailureClass.SEMANTIC
    assert planner.classify("evidence_gap") is FailureClass.EVIDENCE_GAP
    assert planner.classify("unknown_tag") is FailureClass.UNKNOWN


def test_correction_is_bounded():
    planner = SelfCorrectionPlanner()
    plan = planner.plan("claim", meta_tag="semantic_reject", retry_index=2, max_retries=2)
    assert plan.exhausted
    assert plan.signal.safe_to_reuse is False


def test_ethical_failure_cannot_become_execution_instruction():
    planner = SelfCorrectionPlanner()
    plan = planner.plan("unsafe request", meta_tag="ethical", retry_index=0)
    assert plan.failure_class is FailureClass.ETHICAL
    assert "SAFE ALTERNATIVE" in plan.reframed
    assert plan.signal.safe_to_reuse is False


def test_evidence_gap_requires_evidence_or_abstention():
    planner = SelfCorrectionPlanner()
    plan = planner.plan("unsupported claim", meta_tag="evidence_gap")
    assert plan.failure_class is FailureClass.EVIDENCE_GAP
    assert "EVIDENCE REQUIRED" in plan.reframed
