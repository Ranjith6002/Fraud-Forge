from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


VALID_RULE_TYPES = {"VELOCITY", "AMOUNT", "UNUSUAL_AMOUNT", "GEO", "IMPOSSIBLE_GEO", "DEVICE_MISMATCH"}


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64, examples=["High Frequency Alert"])
    rule_type: str = Field(examples=["VELOCITY"])
    description: str = Field(min_length=1, max_length=256, examples=["Flags user with > 3 tx in 5 mins"])
    enabled: bool = Field(default=True)
    risk_score: int = Field(default=30, ge=1, le=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Rule name cannot be empty.")
        return v.strip()

    @field_validator("rule_type")
    @classmethod
    def _valid_type(cls, v: str) -> str:
        upper = v.upper().strip()
        if upper not in VALID_RULE_TYPES:
            raise ValueError(f"Unsupported rule type '{v}'. Supported: {sorted(VALID_RULE_TYPES)}")
        return upper

    @model_validator(mode="after")
    def _validate_parameters(self):
        t = self.rule_type
        p = self.parameters or {}

        if t == "VELOCITY":
            max_tx = p.get("max_transactions", p.get("threshold"))
            win_min = p.get("window_minutes", p.get("window"))
            if max_tx is None or float(max_tx) <= 0:
                raise ValueError("VELOCITY rule requires 'max_transactions' or 'threshold' > 0")
            if win_min is None or float(win_min) <= 0:
                raise ValueError("VELOCITY rule requires 'window_minutes' > 0")
            p["max_transactions"] = int(max_tx)
            p["window_minutes"] = float(win_min)

        elif t in ("AMOUNT", "UNUSUAL_AMOUNT"):
            mult = p.get("multiplier")
            if mult is None or float(mult) <= 0:
                raise ValueError("AMOUNT rule requires 'multiplier' > 0")
            p["multiplier"] = float(mult)
            p["min_history"] = int(p.get("min_history", 3))

        elif t in ("GEO", "IMPOSSIBLE_GEO"):
            spd = p.get("max_speed_kmh", p.get("maximum_speed_kmh"))
            if spd is None or float(spd) <= 0:
                raise ValueError("GEO rule requires 'max_speed_kmh' > 0")
            p["max_speed_kmh"] = float(spd)
            p["min_distance_km"] = float(p.get("min_distance_km", 50.0))

        self.parameters = p
        return self


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=256)
    enabled: Optional[bool] = None
    risk_score: Optional[int] = Field(default=None, ge=1, le=100)
    parameters: Optional[Dict[str, Any]] = None


class RuleOut(BaseModel):
    id: int
    name: str
    rule_type: str
    description: str
    enabled: bool
    risk_score: int
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
