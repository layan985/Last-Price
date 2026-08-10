from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from .config import INFERENCE_FEATURES, MODEL_DIR, RANDOM_STATE
from .features import build_preprocessor


@dataclass
class Split:
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff: pd.Timestamp


def temporal_group_split(df: pd.DataFrame, test_fraction: float = 0.25) -> Split:
    """Hold out the newest complete scenarios.

    The timestamp is constant inside scenario_id, so sorting scenarios by timestamp and splitting
    on scenario groups creates a time-aware holdout without placing related treatment rows on both
    sides.
    """
    scenario_time = (
        df[["scenario_id", "timestamp"]]
        .drop_duplicates("scenario_id")
        .sort_values(["timestamp", "scenario_id"])
        .reset_index(drop=True)
    )
    n_test = max(1, int(np.ceil(len(scenario_time) * test_fraction)))
    test_ids = set(scenario_time.tail(n_test)["scenario_id"].tolist())
    train = df[~df["scenario_id"].isin(test_ids)].copy()
    test = df[df["scenario_id"].isin(test_ids)].copy()
    cutoff = pd.to_datetime(scenario_time.iloc[-n_test]["timestamp"])
    if set(train["scenario_id"]).intersection(set(test["scenario_id"])):
        raise AssertionError("Scenario leakage detected across train/test.")
    return Split(train=train, test=test, cutoff=cutoff)


def _regression_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _classification_metrics(y_true, prob, pred) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "f1": float(f1_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, prob)),
    }
    if len(np.unique(y_true)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, prob))
    else:
        metrics["roc_auc"] = float("nan")
    return metrics


def train_models(df: pd.DataFrame, model_dir: Path = MODEL_DIR) -> dict[str, Any]:
    model_dir.mkdir(parents=True, exist_ok=True)
    split = temporal_group_split(df)

    # Agreement classifier: every negotiation stays in scope. No realized-price fields are inputs.
    X_train = split.train[INFERENCE_FEATURES]
    X_test = split.test[INFERENCE_FEATURES]
    y_train = split.train["agreed"].astype(int)
    y_test = split.test["agreed"].astype(int)

    agreement_baseline = DummyClassifier(strategy="prior")
    agreement_baseline.fit(X_train, y_train)
    base_prob = agreement_baseline.predict_proba(X_test)[:, 1]
    base_pred = agreement_baseline.predict(X_test)

    agreement_model = Pipeline(
        [
            ("prep", build_preprocessor()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=350,
                    min_samples_leaf=4,
                    class_weight="balanced_subsample",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    agreement_model.fit(X_train, y_train)
    agreement_prob = agreement_model.predict_proba(X_test)[:, 1]
    agreement_pred = (agreement_prob >= 0.5).astype(int)

    # Price regression: fit/evaluate only on completed transactions, but split boundaries are
    # inherited from the full scenario-level temporal holdout.
    price_train = split.train[split.train["agreed"] == 1].copy()
    price_test = split.test[split.test["agreed"] == 1].copy()
    Xp_train = price_train[INFERENCE_FEATURES]
    Xp_test = price_test[INFERENCE_FEATURES]
    yp_train = price_train["price"].astype(float)
    yp_test = price_test["price"].astype(float)

    price_baseline = DummyRegressor(strategy="median")
    price_baseline.fit(Xp_train, yp_train)
    price_base_pred = price_baseline.predict(Xp_test)

    price_model = Pipeline(
        [
            ("prep", build_preprocessor()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=400,
                    min_samples_leaf=2,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    price_model.fit(Xp_train, yp_train)
    price_pred = price_model.predict(Xp_test)

    # A lightweight rounds expectation used by the policy layer. It is deliberately not a model
    # input because rounds is an outcome observed after negotiation.
    round_means = (
        split.train.groupby(["buyer_model", "market_segment"], dropna=False)["rounds"]
        .mean()
        .to_dict()
    )

    joblib.dump(agreement_model, model_dir / "agreement_model.joblib")
    joblib.dump(price_model, model_dir / "price_model.joblib")
    joblib.dump(round_means, model_dir / "round_means.joblib")

    metrics = {
        "split": {
            "cutoff": str(split.cutoff),
            "train_rows": int(len(split.train)),
            "test_rows": int(len(split.test)),
            "train_scenarios": int(split.train["scenario_id"].nunique()),
            "test_scenarios": int(split.test["scenario_id"].nunique()),
            "scenario_overlap": int(
                len(set(split.train["scenario_id"]).intersection(set(split.test["scenario_id"])))
            ),
        },
        "agreement": {
            "baseline": _classification_metrics(y_test, base_prob, base_pred),
            "random_forest": _classification_metrics(y_test, agreement_prob, agreement_pred),
        },
        "price": {
            "baseline": _regression_metrics(yp_test, price_base_pred),
            "random_forest": _regression_metrics(yp_test, price_pred),
            "n_train_completed": int(len(price_train)),
            "n_test_completed": int(len(price_test)),
        },
    }

    predictions = split.test[["scenario_id", "treatment_id", "agreed"]].copy()
    predictions["agreement_probability"] = agreement_prob
    predictions["agreement_prediction"] = agreement_pred
    price_predictions = price_test[["scenario_id", "treatment_id", "price"]].copy()
    price_predictions["price_prediction"] = price_pred

    return {
        "agreement_model": agreement_model,
        "price_model": price_model,
        "round_means": round_means,
        "metrics": metrics,
        "split": split,
        "agreement_predictions": predictions,
        "price_predictions": price_predictions,
    }


def load_models(model_dir: Path = MODEL_DIR):
    return (
        joblib.load(model_dir / "agreement_model.joblib"),
        joblib.load(model_dir / "price_model.joblib"),
        joblib.load(model_dir / "round_means.joblib"),
    )
