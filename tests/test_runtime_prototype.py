from anne import AnneRuntime, DevelopmentDecision, DevelopmentSupervisor, run


def test_runtime_uses_local_motor_for_basic_math():
    result = run("2 + 3")
    assert result.output_text == "Sonuç: 5"
    assert result.motor == "deterministic_math"
    assert result.external_authority_used is False
    assert result.trace == ("OBSERVE", "CLASSIFY", "EXECUTE", "RESPOND")


def test_runtime_uses_local_language_for_simple_question():
    result = AnneRuntime().run("Sen nasılsın?")
    assert result.motor == "deterministic_turkish"
    assert result.external_authority_used is False
    assert result.output_text


def test_mitos_proposes_bounded_improvement_without_promotion():
    runtime = AnneRuntime()
    proposals = runtime.develop("Türkçe soru anlama motorunu geliştir", batch_size=3)
    assert len(proposals) == 3
    assert all(p.decision == DevelopmentDecision.PROPOSE for p in proposals)
    assert all("sandbox" in " ".join(p.required_tests) for p in proposals)


def test_promotion_requires_every_gate():
    assert DevelopmentSupervisor.promotion_allowed(
        regression_passed=True,
        capability_passed=True,
        sandbox_passed=True,
        policy_passed=True,
        rollback_ready=True,
    )
    assert not DevelopmentSupervisor.promotion_allowed(
        regression_passed=True,
        capability_passed=True,
        sandbox_passed=False,
        policy_passed=True,
        rollback_ready=True,
    )


def test_missing_evidence_rejects_promotion():
    assert DevelopmentSupervisor.decision_from_evidence() == DevelopmentDecision.REJECT
    assert DevelopmentSupervisor.decision_from_evidence(tests=True, policy=False) == DevelopmentDecision.REJECT
