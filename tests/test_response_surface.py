from dataclasses import dataclass

from anne.response_surface import ResponseComposer


@dataclass
class Result:
    status: str = "EXECUTED"
    verdict: str = "GREEN"
    action: str = "CONTINUE"
    reason: str = ""


def test_greeting_is_turkish() -> None:
    response = ResponseComposer().compose("Merhaba ANNE", Result())
    assert response == "Merhaba. Seni dinliyorum. Nasıl yardımcı olabilirim?"


def test_how_are_you_is_turkish() -> None:
    response = ResponseComposer().compose("Bugün nasılsın?", Result())
    assert response.startswith("İyiyim.")


def test_internal_ethics_values_are_not_exposed() -> None:
    result = Result(reason="Goodness=1.000, Equality=1.000 high. Harm=0.236 acceptable.")
    response = ResponseComposer().compose("hello", result)
    assert "Goodness" not in response
    assert "Equality" not in response
    assert "Harm" not in response


def test_agency_gate_remains_explicit() -> None:
    result = Result(status="ABORTED", action="HALT", reason="agency gate")
    response = ResponseComposer().compose("Bunu yap", result)
    assert "yetki sınırı" in response


def test_bounded_result_requests_more_evidence() -> None:
    result = Result(status="BOUNDED", verdict="BOUNDED", action="STOP")
    response = ResponseComposer().compose("Bunu kesinleştir", result)
    assert "kanıt" in response


def test_response_surface_does_not_change_result() -> None:
    result = Result(reason="Goodness=1.000")
    before = result.__dict__.copy()
    ResponseComposer().compose("Merhaba", result)
    assert result.__dict__ == before
