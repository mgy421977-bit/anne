from anne.calculation.memory_policy import MemoryClass, classify_information
from anne.calculation.methodology import CalculationMethod
from anne.engineering.dxf import DxfDrawing
from anne.simulation import CognitiveSimulator, SimulatedWorld


def test_simulation_records_prediction_error():
    sim = CognitiveSimulator(world=SimulatedWorld(), policy=lambda _: "stabilize")
    experience = sim.step()
    assert experience["prediction_error"] > 0
    assert sim.metrics.predictions == 1
    assert len(sim.experiences) == 1


def test_memory_policy_keeps_weather_ephemeral():
    assert classify_information(category="weather") is MemoryClass.EPHEMERAL
    assert classify_information(category="research", research=True) is MemoryClass.KNOWLEDGE
    assert classify_information(category="calculation", procedural=True) is MemoryClass.PROCEDURAL


def test_calculation_method_can_be_backtested_and_versioned():
    method = CalculationMethod(
        method_id="simple_payback",
        version="1.0.0",
        formula=lambda x: x["capex"] / x["annual_savings"],
        assumptions={"constant_annual_savings": "true"},
        sources=("user_workbook",),
    )
    result = method.calculate({"capex": 1000, "annual_savings": 250})
    assert result.value == 4.0
    assert method.compare({"capex": 1000, "annual_savings": 250}, 4.0) == 0
    assert result.method_version == "1.0.0"


def test_dxf_generator_emits_openable_ascii_structure():
    drawing = DxfDrawing()
    drawing.add_line(0, 0, 100, 0)
    drawing.add_text("ANNE", 10, 10)
    content = drawing.to_ascii()
    assert "SECTION" in content
    assert "ENTITIES" in content
    assert "LINE" in content
    assert "TEXT" in content
    assert content.endswith("0\nEOF\n")
