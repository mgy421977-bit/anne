from anne.core.ambiguity import AmbiguityBoundary, AmbiguityLevel


def test_low_ambiguity_continues():
    decision = AmbiguityBoundary.decide(0.20)
    assert decision.level is AmbiguityLevel.LOW
    assert decision.action == "CONTINUE"


def test_medium_ambiguity_requests_clarification():
    decision = AmbiguityBoundary.decide(0.60)
    assert decision.level is AmbiguityLevel.MEDIUM
    assert decision.action == "CLARIFY"


def test_high_ambiguity_abstains():
    decision = AmbiguityBoundary.decide(0.90)
    assert decision.level is AmbiguityLevel.HIGH
    assert decision.action == "ABSTAIN"


def test_boundary_thresholds_are_deterministic():
    assert AmbiguityBoundary.classify(0.49) is AmbiguityLevel.LOW
    assert AmbiguityBoundary.classify(0.50) is AmbiguityLevel.MEDIUM
    assert AmbiguityBoundary.classify(0.74) is AmbiguityLevel.MEDIUM
    assert AmbiguityBoundary.classify(0.75) is AmbiguityLevel.HIGH


def test_out_of_range_scores_are_clamped():
    assert AmbiguityBoundary.classify(-1.0) is AmbiguityLevel.LOW
    assert AmbiguityBoundary.classify(2.0) is AmbiguityLevel.HIGH


def test_ambiguity_is_not_confidence():
    low = AmbiguityBoundary.decide(0.20)
    high = AmbiguityBoundary.decide(0.90)
    assert low.action == "CONTINUE"
    assert high.action == "ABSTAIN"
    assert low.reason != high.reason
