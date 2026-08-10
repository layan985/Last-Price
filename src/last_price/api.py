from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import INFERENCE_FEATURES
from .models import load_models
from .policy import PolicyWeights, score_candidates

app = FastAPI(title="Last Price ML API", version="0.2.0")


class MarketFeatures(BaseModel):
    buyer_model: str = "buyer_B"
    seller_model: str = "seller_A"
    market_segment: str
    city: str
    season: str
    product_id: str
    shock_flag: int = 0
    cost_shock_pct: float = 0.0
    buyer_value: float
    base_seller_cost: float
    seller_cost: float
    reference_price: float
    gains_from_trade: float
    reference_markup_over_cost: float
    value_premium_over_reference: float
    inventory_level: int = Field(ge=0)
    inventory_velocity: float = Field(ge=0)
    stockout_risk: float = Field(ge=0, le=1)
    competitor_price: float = Field(gt=0)
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    month: int = Field(ge=1, le=12)


@lru_cache(maxsize=1)
def _models():
    return load_models()


@app.get("/health")
def health():
    return {"status": "ok", "service": "last-price", "version": "0.2.0"}


@app.post("/predict/agreement")
def predict_agreement(features: MarketFeatures):
    agreement, _, _ = _models()
    frame = pd.DataFrame([features.model_dump()])
    prob = float(agreement.predict_proba(frame[INFERENCE_FEATURES])[:, 1][0])
    return {"agreement_probability": prob, "model": "agreement-rf-v0.2.0"}


@app.post("/predict/price")
def predict_price(features: MarketFeatures):
    _, price, _ = _models()
    frame = pd.DataFrame([features.model_dump()])
    pred = float(price.predict(frame[INFERENCE_FEATURES])[0])
    return {"predicted_price_if_agreed": pred, "model": "price-rf-v0.2.0"}


class PolicyRequest(BaseModel):
    base: MarketFeatures
    candidate_buyers: list[str] = ["buyer_A", "buyer_B", "buyer_C"]
    deadlock_penalty: float = 8.0
    round_cost: float = 0.35


@app.post("/recommend/policy")
def recommend_policy(request: PolicyRequest):
    agreement, price, round_means = _models()
    rows = []
    base = request.base.model_dump()
    for buyer in request.candidate_buyers:
        row = dict(base)
        row["buyer_model"] = buyer
        rows.append(row)
    candidates = pd.DataFrame(rows)
    scored = score_candidates(
        candidates,
        agreement,
        price,
        round_means,
        PolicyWeights(request.deadlock_penalty, request.round_cost),
    )
    best = scored.sort_values("policy_score", ascending=False).iloc[0]
    return {
        "recommended_buyer_policy": str(best["buyer_model"]),
        "agreement_probability": float(best["pred_agreement_probability"]),
        "predicted_price_if_agreed": float(best["pred_price_if_agreed"]),
        "policy_score": float(best["policy_score"]),
    }
