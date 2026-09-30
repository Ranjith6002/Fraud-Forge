from typing import Any, Dict, Optional

from app.domain import RuleResult, TransactionContext, TransactionData
from app.rules.base import FraudRule
from app.utils.formatting import format_duration
from app.utils.geo import haversine_km


class ImpossibleGeoRule(FraudRule):
    """Consecutive transactions too far apart for the elapsed time (impossible travel)."""

    name = "IMPOSSIBLE_GEO"
    description = "Travel speed between consecutive transactions exceeds a physical limit."

    def __init__(
        self,
        max_speed_kmh: float = 900.0,
        min_distance_km: float = 50.0,
        min_elapsed_seconds: float = 1.0,
        score: int = 40,
    ) -> None:
        super().__init__(score)
        self.max_speed_kmh = max_speed_kmh
        self.min_distance_km = min_distance_km
        self.min_elapsed_seconds = max(min_elapsed_seconds, 0.001)

    def parameters(self) -> Dict[str, Any]:
        return {"max_speed_kmh": self.max_speed_kmh, "min_distance_km": self.min_distance_km}

    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RuleResult:
        ts = transaction.utc_timestamp
        if ts is None:
            return self.miss("Transaction has no valid timestamp.")
        if not transaction.has_coordinates:
            return self.miss("Transaction has no valid coordinates.")

        previous: Optional[TransactionData] = None
        for item in reversed(context.history_before(transaction)):  # newest first
            if item.has_coordinates:
                previous = item
                break
        if previous is None:
            return self.miss("No earlier located transaction for this user.")

        distance = haversine_km(
            float(previous.latitude), float(previous.longitude),
            float(transaction.latitude), float(transaction.longitude),
        )
        if distance < self.min_distance_km:
            return self.miss(f"Same area as previous transaction ({distance:.0f} km apart).")

        elapsed = max((ts - previous.utc_timestamp).total_seconds(), self.min_elapsed_seconds)
        speed = distance / (elapsed / 3600.0)
        if speed > self.max_speed_kmh:
            origin = previous.location or "previous location"
            dest = transaction.location or "current location"
            return self.hit(
                f"Travel from {origin} to {dest} ({distance:,.0f} km) in {format_duration(elapsed)} "
                f"requires ~{speed:,.0f} km/h, above the {self.max_speed_kmh:,.0f} km/h limit.",
                distance_km=round(distance, 1),
                elapsed_seconds=round(elapsed, 1),
                required_speed_kmh=round(speed, 1),
                previous_transaction_id=previous.transaction_id,
            )
        return self.miss(
            f"Travel of {distance:,.0f} km in {format_duration(elapsed)} needs ~{speed:,.0f} km/h "
            "(plausible)."
        )
