"""Small deterministic world used to validate observation, action and error loops."""

from dataclasses import dataclass, field


@dataclass
class SimulatedWorld:
    """A bounded energy-efficiency world with hidden but deterministic dynamics."""

    energy_price: float = 10.0
    efficiency: float = 0.50
    step_count: int = 0
    history: list[dict[str, float | int]] = field(default_factory=list)

    def observe(self) -> dict[str, float | int]:
        return {
            "energy_price": self.energy_price,
            "efficiency": self.efficiency,
            "step": self.step_count,
        }

    def apply(self, action: str) -> dict[str, float | int | str]:
        if action == "optimize":
            # Deliberately non-obvious: optimization helps only after a threshold.
            delta = 0.10 if self.energy_price >= 12.0 else -0.05
            self.efficiency = min(1.0, max(0.0, self.efficiency + delta))
        elif action == "stabilize":
            self.efficiency = min(1.0, self.efficiency + 0.02)
        elif action == "wait":
            pass
        else:
            raise ValueError(f"Unknown simulated action: {action}")

        self.step_count += 1
        observation = self.observe()
        self.history.append(observation.copy())
        return {"action": action, **observation}

    def perturb(self, energy_price: float) -> None:
        """Change an external condition without changing ANNE's memory."""
        self.energy_price = energy_price
