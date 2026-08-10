from __future__ import annotations
from dataclasses import replace
import hashlib, json
import numpy as np
from .agents import MechanicalNegotiator, PolicySpec
from .models import EconomicState, NegotiationOutcome, OfferEvent

class NegotiationEngine:
    """Alternating-offer bilateral bargaining engine with event logging."""
    def run(self,state:EconomicState,buyer:PolicySpec,seller:PolicySpec,*,repetition:int=0,seed:int=0,treatment_id:str|None=None)->NegotiationOutcome:
        state.validate(); buyer.validate(); seller.validate()
        b=MechanicalNegotiator(buyer,"buyer",state,np.random.default_rng(np.random.SeedSequence([seed,repetition,1])))
        s=MechanicalNegotiator(seller,"seller",state,np.random.default_rng(np.random.SeedSequence([seed,repetition,2])))
        if treatment_id is None:
            raw=json.dumps({"b":buyer.name,"s":seller.name,"r":repetition,"seed":seed},sort_keys=True)
            treatment_id=hashlib.sha1(raw.encode()).hexdigest()[:12]
        events=[]; agreed_price=None; used_rounds=state.max_rounds
        for rnd in range(1,state.max_rounds+1):
            bid=round(b.target(rnd),6); seller_threshold=round(s.target(rnd),6); events.append(OfferEvent(rnd,"buyer","offer",bid,None))
            if bid>=seller_threshold:
                agreed_price=bid; events.append(OfferEvent(rnd,"seller","accept",bid,seller_threshold)); used_rounds=rnd; break
            events.append(OfferEvent(rnd,"seller","reject",bid,seller_threshold))
            ask=round(s.target(rnd),6); buyer_threshold=round(b.target(rnd),6); events.append(OfferEvent(rnd,"seller","counter",ask,None))
            if ask<=buyer_threshold:
                agreed_price=ask; events.append(OfferEvent(rnd,"buyer","accept",ask,buyer_threshold)); used_rounds=rnd; break
            events.append(OfferEvent(rnd,"buyer","reject",ask,buyer_threshold))
        agreed=agreed_price is not None
        if agreed:
            buyer_surplus=max(state.buyer_value-agreed_price,0.0); seller_surplus=max(agreed_price-state.seller_cost,0.0)
        else:
            buyer_surplus=state.buyer_outside_option; seller_surplus=state.seller_outside_option
        return NegotiationOutcome(treatment_id,repetition,seed,buyer.name,seller.name,agreed,agreed_price,used_rounds,state.buyer_value,state.seller_cost,state.reference_price,buyer_surplus,seller_surplus,buyer_surplus+seller_surplus,tuple(events))
    @staticmethod
    def shock_cost(state:EconomicState,pct:float)->EconomicState:
        if pct<=-1: raise ValueError("pct must be greater than -1")
        return replace(state,seller_cost=state.seller_cost*(1+pct))
