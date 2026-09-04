from __future__ import annotations

from anne.neuro_symbolic.audit import PlanStep
from anne.safety.policy import ToolPolicy, redact_sensitive
from anne.world.model import Belief
from anne.world.revision import BeliefRevision, CausalHypothesis


def test_redact_sensitive_removes_common_credentials() -> None:
    value = redact_sensitive("api_key=sk_test_abcdefghijklmnop password: hunter2")
    assert "sk_test_abcdefghijklmnop" not in value
    assert "hunter2" not in value
    assert "[REDACTED]" in value


def test_tool_policy_allows_read_tools_and_blocks_writes_or_escape() -> None:
    policy = ToolPolicy()
    assert policy.authorize("local_read", {"path": "notes.txt"}).allowed
    assert not policy.authorize("shell_exec", {}).allowed
    assert not policy.authorize("local_read", {"path": "../secret"}).allowed


def test_belief_revision_scales_confidence_and_records_causal_support() -> None:
    revision = BeliefRevision()
    belief = revision.revise(Belief("a", "causes", "b", 0.9), source_reliability=0.5)
    assert belief.confidence == 0.45
    causal = revision.add_causal(
        CausalHypothesis("a", "b", "mechanism", 0.8, ["e1"])
    )
    assert causal.status == "supported"


def test_plan_repair_is_created_for_missing_preconditions() -> None:
    step = PlanStep("p1", "deploy", preconditions=["approved"])
    assert step.check_preconditions(set()) is False
    repair = step.repair(["approved"])
    assert repair.action == "gather missing prerequisites"
    assert repair.expected_effects == ["approved"]
