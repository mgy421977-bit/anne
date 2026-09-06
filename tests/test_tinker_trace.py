from desktop.anne_tinker import AnneTinker


def test_tinker_extracts_symbolic_math() -> None:
    assert AnneTinker._extract_math_expression("12 + 30") == "12 + 30"


def test_tinker_extracts_turkish_math() -> None:
    assert AnneTinker._extract_math_expression("12 artı 30") == "12 + 30"


def test_tinker_rejects_non_math_expression() -> None:
    assert AnneTinker._extract_math_expression("bana bir kahve yap") is None
