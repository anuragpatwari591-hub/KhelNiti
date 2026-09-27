from datetime import datetime

from pydantic import BaseModel


class OddsSnapshotOut(BaseModel):
    market: str
    selection: str
    price: float
    implied_probability: float
    source: str
    captured_at: datetime

    model_config = {"from_attributes": True}


class MarketMovementOut(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}

    market: str
    selection: str
    opening_price: float
    current_price: float
    price_change_pct: float
    market_implied_probability: float
    model_probability: float | None
    divergence: float | None
    computed_at: datetime
