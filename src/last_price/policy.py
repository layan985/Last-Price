from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import INFERENCE_FEATURES


@dataclass
class PolicyWeights:
    deadlock_penalty: float = 8.0
    round_cost: float = 0.35


def score_candidates(candidates, agreement_model, price_model, round_means, weights=PolicyWeights()):
    frame = candidates.copy()
    p_agree = agreement_model.predict_proba(frame[INFERENCE_FEATURES])[:, 1]
    pred_price = price_model.predict(frame[INFERENCE_FEATURES])
    expected_rounds = [
        float(round_means.get((r.buyer_model, r.market_segment), 4.0))
        for r in frame.itertuples()
    ]
    expected_surplus_if_trade = np.maximum(frame["buyer_value"].to_numpy() - pred_price, 0)
    frame["pred_agreement_probability"] = p_agree
    frame["pred_price_if_agreed"] = pred_price
    frame["expected_rounds"] = expected_rounds
    frame["policy_score"] = (
        p_agree * expected_surplus_if_trade
        - (1 - p_agree) * weights.deadlock_penalty
        - np.asarray(expected_rounds) * weights.round_cost
    )
    return frame


def evaluate_policy(test, agreement_model, price_model, round_means, baseline_buyer="buyer_B"):
    scored = score_candidates(test, agreement_model, price_model, round_means)
    key = ["scenario_id", "seller_model"]
    chosen_idx = scored.groupby(key)["policy_score"].idxmax()
    chosen = test.loc[chosen_idx].copy()

    baseline = test[test["buyer_model"] == baseline_buyer].copy()
    # Each scenario × seller has exactly one baseline buyer row in the current design.
    baseline = baseline.sort_values(key)
    chosen = chosen.sort_values(key)

    def summarize(frame):
        completed = frame[frame["agreed"] == 1]
        return {
            "rows": len(frame),
            "agreement_rate": float(frame["agreed"].mean()),
            "mean_price_if_agreed": float(completed["price"].mean()) if len(completed) else None,
            "mean_buyer_surplus": float(frame["buyer_surplus"].mean()),
            "mean_rounds": float(frame["rounds"].mean()),
            "composite_realized_utility": float(
                (
                    frame["buyer_surplus"]
                    - (1 - frame["agreed"]) * 8.0
                    - frame["rounds"] * 0.35
                ).mean()
            ),
        }

    recommended_summary = summarize(chosen)
    baseline_summary = summarize(baseline)

    uplift = {}
    for metric in [
        "agreement_rate",
        "mean_price_if_agreed",
        "mean_buyer_surplus",
        "mean_rounds",
        "composite_realized_utility",
    ]:
        a, b = recommended_summary[metric], baseline_summary[metric]
        uplift[metric] = None if a is None or b is None else float(a - b)

    return {
        "baseline_policy": baseline_buyer,
        "recommended": recommended_summary,
        "baseline": baseline_summary,
        "absolute_uplift": uplift,
        "selection_share": {
            str(k): float(v)
            for k, v in chosen["buyer_model"].value_counts(normalize=True).sort_index().items()
        },
    }
