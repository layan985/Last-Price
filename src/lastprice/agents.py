from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .models import EconomicState

@dataclass(frozen=True)
class PolicySpec:
    name: str
    anchor_strength: float = 0.35
    concession_rate: float = 0.22
    acceptance_slack: float = 0.00
    noise_sd: float = 0.00
    def validate(self) -> None:
        if not (0 <= self.anchor_strength <= 1): raise ValueError("anchor_strength must be in [0, 1]")
        if not (0 <= self.concession_rate <= 1): raise ValueError("concession_rate must be in [0, 1]")
        if self.acceptance_slack < 0: raise ValueError("acceptance_slack must be >= 0")
        if self.noise_sd < 0: raise ValueError("noise_sd must be >= 0")

class MechanicalNegotiator:
    """Transparent test policy. Not an LLM."""
    def __init__(self, spec: PolicySpec, role: str, state: EconomicState, rng: np.random.Generator):
        if role not in {"buyer", "seller"}: raise ValueError("role must be buyer or seller")
        spec.validate(); self.spec=spec; self.role=role; self.state=state; self.rng=rng
    def _noise(self) -> float:
        return 0.0 if self.spec.noise_sd == 0 else float(self.rng.normal(0, self.spec.noise_sd))
    def target(self, round_number: int) -> float:
        r=max(round_number-1,0)
        if self.role == "buyer":
            initial=min(self.state.reference_price*(1-0.45*self.spec.anchor_strength), self.state.buyer_value)
            target=self.state.buyer_value-(self.state.buyer_value-initial)*((1-self.spec.concession_rate)**r)+self._noise()
            return float(np.clip(target,0,self.state.buyer_value))
        initial=max(self.state.reference_price*(1+0.45*self.spec.anchor_strength), self.state.seller_cost)
        target=self.state.seller_cost+(initial-self.state.seller_cost)*((1-self.spec.concession_rate)**r)+self._noise()
        return float(max(target,self.state.seller_cost))
    def accepts(self, incoming_price: float, round_number: int) -> bool:
        threshold=self.target(round_number)
        if self.role == "buyer": return incoming_price <= min(self.state.buyer_value, threshold*(1+self.spec.acceptance_slack))
        return incoming_price >= max(self.state.seller_cost, threshold*(1-self.spec.acceptance_slack))
