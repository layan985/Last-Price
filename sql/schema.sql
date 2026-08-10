-- Portable SQLite/PostgreSQL-style analytical schema for the portfolio dataset.
CREATE TABLE IF NOT EXISTS negotiations (
    scenario_id INTEGER NOT NULL,
    treatment_id TEXT PRIMARY KEY,
    repetition INTEGER NOT NULL,
    seed INTEGER NOT NULL,
    buyer_model TEXT NOT NULL,
    seller_model TEXT NOT NULL,
    market_segment TEXT NOT NULL,
    shock_flag INTEGER NOT NULL,
    cost_shock_pct REAL NOT NULL,
    buyer_value REAL NOT NULL,
    base_seller_cost REAL NOT NULL,
    seller_cost REAL NOT NULL,
    reference_price REAL NOT NULL,
    gains_from_trade REAL NOT NULL,
    agreed INTEGER NOT NULL,
    price REAL,
    rounds INTEGER NOT NULL,
    city TEXT NOT NULL,
    product_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    inventory_level INTEGER NOT NULL,
    inventory_velocity REAL NOT NULL,
    stockout_risk REAL NOT NULL,
    competitor_price REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_negotiations_scenario ON negotiations(scenario_id);
CREATE INDEX IF NOT EXISTS idx_negotiations_time ON negotiations(timestamp);
CREATE INDEX IF NOT EXISTS idx_negotiations_models ON negotiations(buyer_model, seller_model);
