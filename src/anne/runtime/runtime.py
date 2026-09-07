"""Primary ANNE v0.1 runtime interface."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from anne.windows.cli import AnneConsole

from .supervisor import DevelopmentProposal, DevelopmentSupervisor


@dataclass(frozen=True)
class RuntimeResult:
    """Traceable result from one bounded runtime turn."""

    input_text: str
    output_text: str
    motor: str
    external_authority_used: bool = False
    trace: tuple[str, ...] = ()


@dataclass
class AnneRuntime:
    """Executive shell around ANNE's deterministic prototype motors.

    Basic language, mathematics and weather routing stay local. External models
    are intentionally outside this first runtime and may later be attached as an
    advisor/research layer without becoming the authority for deterministic tasks.
    """

    console: AnneConsole = field(default_factory=AnneConsole)
    supervisor: DevelopmentSupervisor = field(default_factory=DevelopmentSupervisor)

    def run(self, text: str) -> RuntimeResult:
        """Observe input, select a local motor, execute it, and return a trace."""
        analysis = self.console.language.analyze(text)
        output = self.console.answer(text)
        motor = {
            "math": "deterministic_math",
            "weather": "weather_observation_plus_deterministic_language",
            "question": "deterministic_turkish",
            "statement": "deterministic_turkish",
        }.get(analysis.intent, "deterministic_turkish")
        return RuntimeResult(
            input_text=text,
            output_text=output,
            motor=motor,
            trace=("OBSERVE", "CLASSIFY", "EXECUTE", "RESPOND"),
        )

    def develop(self, goal: str, batch_size: int = 5) -> list[DevelopmentProposal]:
        """Ask MITOS for bounded improvement candidates; do not execute them."""
        return self.supervisor.propose(goal, batch_size=batch_size)


def run(text: str) -> RuntimeResult:
    """Convenience entry point: ``anne.run('Bugün hava nasıl?')``."""
    return AnneRuntime().run(text)


__all__ = ["AnneRuntime", "RuntimeResult", "run"]
