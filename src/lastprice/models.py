from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class EconomicState:
    buyer_value: float
    seller_cost: float
    reference_price: float
    buyer_outside_option: float = 0.0
    seller_outside_option: float = 0.0
    max_rounds: int = 12
    def validate(self) -> None:
        if self.buyer_value <= 0 or self.seller_cost < 0 or self.reference_price <= 0:
            raise ValueError("Prices and valuations must be non-negative, with positive value/reference price.")
        if self.buyer_value <= self.seller_cost:
            raise ValueError("Positive gains from trade required: buyer_value must exceed seller_cost.")
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")

@dataclass(frozen=True)
class OfferEvent:
    round: int
    actor: str
    action: str
    price: float | None
    threshold: float | None

@dataclass(frozen=True)
class NegotiationOutcome:
    treatment_id: str
    repetition: int
    seed: int
    buyer_model: str
    seller_model: str
    agreed: bool
    price: float | None
    rounds: int
    buyer_value: float
    seller_cost: float
    reference_price: float
    buyer_surplus: float
    seller_surplus: float
    total_surplus: float
    transcript: tuple[OfferEvent, ...]
    def flat_dict(self) -> dict[str, Any]:
        out = asdict(self); out.pop("transcript", None); return out
