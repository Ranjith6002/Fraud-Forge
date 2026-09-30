from dataclasses import dataclass

from app.domain import RiskLevel


@dataclass(frozen=True)
class RiskThresholds:
    """Score -> risk level mapping. LOW: 0..medium-1, MEDIUM: medium..high-1, HIGH: high..max."""

    medium: int = 40
    high: int = 70
    max_score: int = 100

    def __post_init__(self) -> None:
        if not (0 < self.medium <= self.high <= self.max_score):
            raise ValueError("Thresholds must satisfy 0 < medium <= high <= max_score")

    def clamp(self, score: int) -> int:
        return max(0, min(int(score), self.max_score))

    def level_for(self, score: int) -> RiskLevel:
        score = self.clamp(score)
        if score >= self.high:
            return RiskLevel.HIGH
        if score >= self.medium:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
