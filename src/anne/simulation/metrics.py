"""Metrics for simulation claims; no learning claim is made without measurement."""

from dataclasses import dataclass, field


@dataclass
class SimulationMetrics:
    predictions: int = 0
    successful_predictions: int = 0
    absolute_errors: list[float] = field(default_factory=list)

    def record(self, predicted: float, observed: float) -> None:
        self.predictions += 1
        error = abs(predicted - observed)
        self.absolute_errors.append(error)
        if error == 0:
            self.successful_predictions += 1

    @property
    def accuracy(self) -> float:
        if not self.predictions:
            return 0.0
        return self.successful_predictions / self.predictions

    @property
    def mean_absolute_error(self) -> float:
        if not self.absolute_errors:
            return 0.0
        return sum(self.absolute_errors) / len(self.absolute_errors)
