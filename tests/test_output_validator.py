from anne.core.output_validator import OutputValidator


def test_dictionary_dump_is_rejected():
    ok, score, reason = OutputValidator.validate(
        "Bess: Look up Bess or BESS in Wiktionary, the free dictionary."
    )
    assert not ok
    assert score == 0.0
    assert reason == "dictionary_or_disambiguation_dump"


def test_instruction_only_output_is_rejected():
    ok, _, reason = OutputValidator.validate("Look up BESS in a dictionary.")
    assert not ok
    assert reason == "instruction_not_answer"


def test_normal_answer_can_pass():
    ok, score, reason = OutputValidator.validate(
        "BESS stands for Battery Energy Storage System."
    )
    assert ok
    assert score >= 0.75
    assert reason == "accepted"
