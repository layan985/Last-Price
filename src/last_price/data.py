from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    DATA_PROCESSED,
    DATA_RAW,
    INFERENCE_FEATURES,
    LEAKAGE_COLUMNS,
    RANDOM_STATE,
    SQLITE_DB,
)

REQUIRED_RAW_COLUMNS = {
    "scenario_id",
    "treatment_id",
    "buyer_model",
    "seller_model",
    "market_segment",
    "shock_flag",
    "cost_shock_pct",
    "buyer_value",
    "base_seller_cost",
    "seller_cost",
    "reference_price",
    "gains_from_trade",
    "agreed",
    "price",
    "rounds",
}

BUYER_MODELS = ("buyer_A", "buyer_B", "buyer_C")
SELLER_MODELS = ("seller_A", "seller_B")


def generate_raw(n_scenarios: int = 500, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Generate the mechanical-policy negotiation benchmark from a fixed seed.

    Each scenario freezes the economic primitives, then crosses three buyer policies with two
    seller policies. Buyer A is more price-aggressive (lower conditional prices, more deadlock and
    rounds); Buyer C is more accommodating (higher completion, higher prices, fewer rounds).
    Seller A is harder than Seller B. These labels are test policies, not commercial LLMs.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    segment_cfg = {
        "wide_margin": (0.45, 0.90),
        "mid_margin": (0.18, 0.45),
        "tight_margin": (0.04, 0.18),
    }
    buyer_capture = {"buyer_A": 0.62, "buyer_B": 0.48, "buyer_C": 0.34}
    buyer_agreement = {"buyer_A": -0.55, "buyer_B": 0.00, "buyer_C": 0.42}
    buyer_rounds = {"buyer_A": 5.0, "buyer_B": 4.0, "buyer_C": 3.0}
    seller_capture_shift = {"seller_A": -0.07, "seller_B": 0.06}
    seller_agreement = {"seller_A": -0.18, "seller_B": 0.16}
    seller_rounds = {"seller_A": 0.7, "seller_B": -0.3}
    segment_capture = {"wide_margin": 0.04, "mid_margin": 0.00, "tight_margin": -0.07}
    segment_agreement = {"wide_margin": 0.65, "mid_margin": 0.05, "tight_margin": -0.85}
    segment_rounds = {"wide_margin": 0.0, "mid_margin": 1.0, "tight_margin": 3.0}

    for sid in range(n_scenarios):
        segment = str(rng.choice(list(segment_cfg), p=[0.47, 0.35, 0.18]))
        lo, hi = segment_cfg[segment]
        base_cost = float(rng.uniform(45.0, 120.0))
        buyer_value = float(base_cost * (1.0 + rng.uniform(lo, hi)))
        reference_share = float(rng.uniform(0.42, 0.62))
        reference_price = float(base_cost + reference_share * (buyer_value - base_cost))
        shock_pct = float(rng.choice([0.0, 0.05, 0.10, 0.15], p=[0.52, 0.15, 0.20, 0.13]))
        seller_cost = float(min(base_cost * (1.0 + shock_pct), buyer_value - 2.5))
        gains = float(buyer_value - seller_cost)
        scenario_capture_noise = float(rng.normal(0.0, 0.035))
        scenario_agreement_noise = float(rng.normal(0.0, 0.35))

        for b_idx, buyer in enumerate(BUYER_MODELS):
            for s_idx, seller in enumerate(SELLER_MODELS):
                pair_rng = np.random.default_rng(seed + sid * 101 + b_idx * 17 + s_idx * 31)
                gains_ratio = gains / max(buyer_value, 1e-9)
                logit = (
                    -0.15
                    + 7.2 * gains_ratio
                    + segment_agreement[segment]
                    + buyer_agreement[buyer]
                    + seller_agreement[seller]
                    - 1.2 * shock_pct
                    + scenario_agreement_noise
                )
                p_agree = float(1.0 / (1.0 + np.exp(-logit)))
                agreed = int(pair_rng.random() < p_agree)

                round_mean = (
                    buyer_rounds[buyer]
                    + seller_rounds[seller]
                    + segment_rounds[segment]
                    + 1.5 * shock_pct
                )
                rounds = int(np.clip(round(round_mean + pair_rng.normal(0.0, 0.8)), 1, 12))
                if not agreed:
                    rounds = int(np.clip(max(rounds, round(round_mean + 2.0)), 2, 12))

                capture = float(
                    np.clip(
                        buyer_capture[buyer]
                        + seller_capture_shift[seller]
                        + segment_capture[segment]
                        + scenario_capture_noise
                        + pair_rng.normal(0.0, 0.025),
                        0.05,
                        0.92,
                    )
                )
                if agreed:
                    price = float(seller_cost + (1.0 - capture) * gains)
                    price += float(pair_rng.normal(0.0, max(0.20, 0.012 * gains)))
                    price = float(np.clip(price, seller_cost, buyer_value))
                    buyer_surplus = float(buyer_value - price)
                    seller_surplus = float(price - seller_cost)
                    total_surplus = float(gains)
                    buyer_capture_rate = float(buyer_surplus / gains) if gains > 0 else np.nan
                    seller_capture_rate = float(seller_surplus / gains) if gains > 0 else np.nan
                    price_vs_reference_pct = float(price / reference_price - 1.0)
                else:
                    price = np.nan
                    buyer_surplus = 0.0
                    seller_surplus = 0.0
                    total_surplus = 0.0
                    buyer_capture_rate = np.nan
                    seller_capture_rate = np.nan
                    price_vs_reference_pct = np.nan

                rows.append(
                    {
                        "scenario_id": sid,
                        "treatment_id": f"scenario={sid}|B={buyer}|S={seller}",
                        "repetition": sid,
                        "seed": seed,
                        "buyer_model": buyer,
                        "seller_model": seller,
                        "market_segment": segment,
                        "shock_flag": int(shock_pct > 0),
                        "cost_shock_pct": shock_pct,
                        "buyer_value": buyer_value,
                        "base_seller_cost": base_cost,
                        "seller_cost": seller_cost,
                        "reference_price": reference_price,
                        "gains_from_trade": gains,
                        "reference_markup_over_cost": float(reference_price / seller_cost - 1.0),
                        "value_premium_over_reference": float(buyer_value / reference_price - 1.0),
                        "agreed": agreed,
                        "price": price,
                        "rounds": rounds,
                        "buyer_surplus": buyer_surplus,
                        "seller_surplus": seller_surplus,
                        "total_surplus": total_surplus,
                        "buyer_capture_rate": buyer_capture_rate,
                        "seller_capture_rate": seller_capture_rate,
                        "price_vs_reference_pct": price_vs_reference_pct,
                    }
                )

    return pd.DataFrame(rows)


def _scenario_feature_frame(scenario_ids: pd.Series) -> pd.DataFrame:
    """Create ex-ante marketplace context deterministically at scenario level."""
    unique = np.sort(pd.unique(scenario_ids.astype(int)))
    rows = []
    cities = ["Amman", "Budapest", "Dubai", "Riyadh", "Cairo"]
    base_date = pd.Timestamp("2025-01-01")
    for sid in unique:
        rng = np.random.default_rng(RANDOM_STATE + int(sid))
        timestamp = base_date + pd.Timedelta(days=int(sid)) + pd.Timedelta(hours=int(rng.integers(8, 22)))
        inventory = int(rng.integers(8, 121))
        velocity = float(rng.uniform(0.5, 18.0))
        stockout = float(np.clip(velocity / max(inventory, 1) + rng.normal(0, 0.01), 0, 1))
        rows.append(
            {
                "scenario_id": int(sid),
                "timestamp": timestamp,
                "city": cities[int(sid) % len(cities)],
                "product_id": f"P{int(sid) % 50:02d}",
                "inventory_level": inventory,
                "inventory_velocity": velocity,
                "stockout_risk": stockout,
            }
        )
    return pd.DataFrame(rows)


def enrich_market_features(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_RAW_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required raw columns: {sorted(missing)}")

    out = df.copy()
    context = _scenario_feature_frame(out["scenario_id"])
    out = out.merge(context, on="scenario_id", how="left", validate="many_to_one")
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=False)
    out["month"] = out["timestamp"].dt.month.astype(int)
    out["day_of_week"] = out["timestamp"].dt.dayofweek.astype(int)
    out["hour"] = out["timestamp"].dt.hour.astype(int)
    out["season"] = np.select(
        [
            out["month"].isin([12, 1, 2]),
            out["month"].isin([3, 4, 5]),
            out["month"].isin([6, 7, 8]),
        ],
        ["winter", "spring", "summer"],
        default="autumn",
    )
    sid_noise = ((out["scenario_id"].astype(int) * 37) % 17 - 8) / 200.0
    out["competitor_price"] = out["reference_price"] * (1.0 + sid_noise)
    return out


def load_raw(path: Path = DATA_RAW) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    df = generate_raw()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


def load_processed(path: Path = DATA_PROCESSED) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["timestamp"])


def build_processed(raw_path: Path = DATA_RAW, output_path: Path = DATA_PROCESSED) -> pd.DataFrame:
    df = enrich_market_features(load_raw(raw_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def dataset_fingerprint(df: pd.DataFrame) -> str:
    canonical = df.sort_values(["scenario_id", "treatment_id"]).to_csv(index=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def data_quality_report(df: pd.DataFrame) -> dict:
    completed_without_price = int(((df["agreed"] == 1) & df["price"].isna()).sum())
    failed_with_price = int(((df["agreed"] == 0) & df["price"].notna()).sum())
    price_below_cost = int(((df["price"].notna()) & (df["price"] < df["seller_cost"] - 1e-9)).sum())
    price_above_value = int(((df["price"].notna()) & (df["price"] > df["buyer_value"] + 1e-9)).sum())
    duplicate_treatment = int(df["treatment_id"].duplicated().sum())
    invalid_rounds = int((df["rounds"] < 1).sum())
    scenario_feature_inconsistency = 0
    for col in [
        "timestamp",
        "city",
        "product_id",
        "inventory_level",
        "inventory_velocity",
        "stockout_risk",
    ]:
        scenario_feature_inconsistency += int((df.groupby("scenario_id")[col].nunique(dropna=False) > 1).sum())

    checks = {
        "rows": int(len(df)),
        "scenarios": int(df["scenario_id"].nunique()),
        "missing_required_features": int(df[INFERENCE_FEATURES].isna().sum().sum()),
        "duplicate_treatment_ids": duplicate_treatment,
        "completed_without_price": completed_without_price,
        "failed_with_price": failed_with_price,
        "price_below_seller_cost": price_below_cost,
        "price_above_buyer_value": price_above_value,
        "invalid_rounds": invalid_rounds,
        "scenario_context_inconsistencies": scenario_feature_inconsistency,
    }
    checks["passed"] = all(v == 0 for k, v in checks.items() if k not in {"rows", "scenarios", "passed"})
    return checks


def leakage_audit(df: pd.DataFrame) -> dict:
    used = set(INFERENCE_FEATURES)
    leaked = sorted(used.intersection(LEAKAGE_COLUMNS))
    missing = sorted(used - set(df.columns))
    return {
        "inference_features": INFERENCE_FEATURES,
        "blacklisted_post_outcome_fields": LEAKAGE_COLUMNS,
        "blacklisted_fields_present_in_training_features": leaked,
        "missing_inference_features": missing,
        "passed": not leaked and not missing,
    }


def build_sqlite_database(df: pd.DataFrame, db_path: Path = SQLITE_DB) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        sql_df = df.copy()
        sql_df["timestamp"] = pd.to_datetime(sql_df["timestamp"]).astype(str)
        sql_df.to_sql("negotiations", conn, index=False, if_exists="replace")
        conn.executescript(
            """
            CREATE INDEX idx_negotiations_scenario ON negotiations(scenario_id);
            CREATE INDEX idx_negotiations_models ON negotiations(buyer_model, seller_model);
            CREATE INDEX idx_negotiations_time ON negotiations(timestamp);
            CREATE TABLE model_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                dataset_sha256 TEXT NOT NULL,
                git_commit TEXT,
                metrics_json TEXT NOT NULL
            );
            CREATE TABLE model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                scenario_id INTEGER NOT NULL,
                treatment_id TEXT NOT NULL,
                target TEXT NOT NULL,
                prediction REAL NOT NULL,
                observed REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES model_runs(run_id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
