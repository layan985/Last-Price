from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "negotiations.csv"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "negotiations_enriched.csv"
SQLITE_DB = PROJECT_ROOT / "artifacts" / "last_price.db"
MODEL_DIR = PROJECT_ROOT / "artifacts" / "models"
REPORT_DIR = PROJECT_ROOT / "reports"
MONITOR_DIR = PROJECT_ROOT / "artifacts" / "monitoring"

CATEGORICAL_FEATURES = [
    "buyer_model",
    "seller_model",
    "market_segment",
    "city",
    "season",
    "product_id",
]

NUMERIC_FEATURES = [
    "shock_flag",
    "cost_shock_pct",
    "buyer_value",
    "base_seller_cost",
    "seller_cost",
    "reference_price",
    "gains_from_trade",
    "reference_markup_over_cost",
    "value_premium_over_reference",
    "inventory_level",
    "inventory_velocity",
    "stockout_risk",
    "competitor_price",
    "hour",
    "day_of_week",
    "month",
]

INFERENCE_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

# These fields are known only after negotiation or are algebraically downstream of the target.
LEAKAGE_COLUMNS = [
    "agreed",
    "price",
    "rounds",
    "buyer_surplus",
    "seller_surplus",
    "total_surplus",
    "buyer_capture_rate",
    "seller_capture_rate",
    "price_vs_reference_pct",
]

RANDOM_STATE = 20260810
