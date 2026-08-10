from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon

from .config import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def population_stability_index(reference, current, bins=10) -> float:
    ref = pd.Series(reference).dropna().astype(float)
    cur = pd.Series(current).dropna().astype(float)
    if ref.empty or cur.empty:
        return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ref_hist, _ = np.histogram(ref, bins=edges)
    cur_hist, _ = np.histogram(cur, bins=edges)
    eps = 1e-6
    ref_pct = np.maximum(ref_hist / max(ref_hist.sum(), 1), eps)
    cur_pct = np.maximum(cur_hist / max(cur_hist.sum(), 1), eps)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def categorical_js(reference, current) -> float:
    ref = pd.Series(reference).astype(str)
    cur = pd.Series(current).astype(str)
    cats = sorted(set(ref.unique()).union(set(cur.unique())))
    rp = ref.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy() + 1e-9
    cp = cur.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy() + 1e-9
    return float(jensenshannon(rp, cp, base=2.0) ** 2)


def monitor_batch(reference: pd.DataFrame, current: pd.DataFrame, agreement_model) -> dict:
    numeric = {}
    for col in NUMERIC_FEATURES:
        numeric[col] = population_stability_index(reference[col], current[col])
    categorical = {}
    for col in CATEGORICAL_FEATURES:
        categorical[col] = categorical_js(reference[col], current[col])

    ref_pred = agreement_model.predict_proba(reference[CATEGORICAL_FEATURES + NUMERIC_FEATURES])[:, 1]
    cur_pred = agreement_model.predict_proba(current[CATEGORICAL_FEATURES + NUMERIC_FEATURES])[:, 1]
    prediction_psi = population_stability_index(ref_pred, cur_pred)

    alerts = []
    for col, value in numeric.items():
        if np.isfinite(value) and value >= 0.2:
            alerts.append({"feature": col, "type": "numeric_psi", "value": value})
    for col, value in categorical.items():
        if np.isfinite(value) and value >= 0.1:
            alerts.append({"feature": col, "type": "categorical_js", "value": value})
    if np.isfinite(prediction_psi) and prediction_psi >= 0.2:
        alerts.append({"feature": "agreement_prediction", "type": "prediction_psi", "value": prediction_psi})

    return {
        "numeric_psi": numeric,
        "categorical_js": categorical,
        "prediction_psi": prediction_psi,
        "alerts": alerts,
        "status": "alert" if alerts else "ok",
    }


def make_drifted_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Stress batch: synthetic inventory shock + city composition shift + competitor repricing."""
    out = df.copy()
    out["inventory_level"] = np.maximum(1, (out["inventory_level"] * 0.35).round()).astype(int)
    out["stockout_risk"] = np.clip(out["stockout_risk"] * 2.5 + 0.08, 0, 1)
    out["competitor_price"] = out["competitor_price"] * 1.15
    idx = out.index[: int(len(out) * 0.65)]
    out.loc[idx, "city"] = "Dubai"
    return out
