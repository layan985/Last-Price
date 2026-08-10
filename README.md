# Last Price

Last Price started with a simple problem: two economically identical buyers can pay different prices if the negotiating policy representing them changes. The research version tests that mechanism. This repository turns the same experiment into a **production-style marketplace data-science system**.

The useful part is not a giant model score. It is the full path from raw negotiations to SQL, leakage-safe training, a decision policy, an API, a model registry and drift alerts.

> **Scope:** the shipped data are synthetic mechanical-policy negotiations. Results are not evidence about real commercial LLMs or a live marketplace.

**Short review path:** [five-minute hiring-manager guide](HIRING_MANAGER_GUIDE.md) · [CV bullets](CV_BULLETS.md) · [stakeholder memo](STAKEHOLDER_MEMO.md) · [technical report](TECHNICAL_REPORT.md)

## What is here

- deterministic generator for 3,000 negotiations across 500 related economic scenarios
- deterministic time/location/product/inventory context for production-style feature work
- SQLite analytical layer with CTEs, windows, segmentation and model-monitoring queries
- agreement classifier + conditional-price regressor
- time-aware, scenario-grouped holdout
- explicit leakage blacklist for post-outcome variables
- held-out policy selection against a fixed buyer-policy baseline
- dataset hashing, run manifests and out-of-sample prediction logging
- FastAPI model serving + Docker
- drift stress test
- transcript → intent → SQL voice-query layer, with optional local Whisper adapter
- image + text + structured feature fusion smoke benchmark
- GitHub Actions rebuild/tests/lint workflow

## Reproduce it

```bash
python -m pip install -e ".[dev]"
python scripts/rebuild_demo.py
pytest
```

Serve the models:

```bash
uvicorn last_price.api:app --reload
```

Then open `/docs`.

## Architecture

```text
deterministic synthetic generator
          |
          v
data/raw/negotiations.csv (generated, gitignored)
          |
          v
point-in-time enrichment -----> data-quality + leakage audit
          |
          +----> SQLite analytics / SQL portfolio
          |
          v
time + scenario group split
    |                 |
    v                 v
agreement model     price model (completed trades)
    \                 /
     \               /
      v             v
      policy scoring
            |
            v
 held-out KPI evaluation
            |
            +----> FastAPI / Docker
            |
            +----> run registry + prediction log
            |
            +----> drift monitoring
```

## Leakage boundary

All treatment rows inside one `scenario_id` share the same underlying state. They cannot be split independently.

Training uses only pre-negotiation features. These fields are banned from the model matrix:

```text
agreed
price
rounds
buyer_surplus
seller_surplus
total_surplus
buyer_capture_rate
seller_capture_rate
price_vs_reference_pct
```

The build fails if a blacklisted field appears in the training feature contract.

## SQL

The database contains `negotiations`, `model_runs` and `model_predictions`.

Examples in `sql/` cover:

- conversion/reliability funnels
- quote-to-value segmentation
- inventory and stockout analysis
- marketplace KPI tables
- CTEs + rolling window functions
- post-deployment prediction monitoring

## MLOps

Every rebuild writes:

- dataset SHA-256
- split metadata
- model metrics against dummy baselines
- run ID and timestamp
- git commit when available
- out-of-sample predictions
- leakage and data-quality audits
- policy KPI report
- drift report

See `MLOPS.md`.

## API

`POST /predict/agreement`

Returns agreement probability.

`POST /predict/price`

Returns expected price conditional on trade.

`POST /recommend/policy`

Scores candidate buyer policies using conversion probability, conditional price, deadlock cost and time cost.

## Voice layer

The voice module has two parts:

```text
audio --optional Whisper--> transcript --> intent/slots --> parameterized SQL
```

The core repo tests transcript parsing and SQL compilation without requiring a heavyweight ASR dependency.

## Multimodal layer

The smoke benchmark fuses:

```text
image statistics + text signals + price + inventory
```

and classifies synthetic listing categories. It exists to exercise a multimodal feature contract and test path. It is deliberately not presented as real-world computer-vision accuracy.

## Current held-out results

The rebuild uses the newest 125 scenarios (750 negotiations) as the test period, with zero `scenario_id` overlap.

| Task | Baseline | Random forest |
|---|---:|---:|
| Agreement ROC-AUC | 0.500 | 0.789 |
| Agreement Brier score | 0.196 | 0.164 |
| Price RMSE | 28.79 | 3.33 |
| Price MAE | 23.72 | 2.54 |

The policy layer is deliberately reported as a tradeoff rather than a victory lap. Against fixed `buyer_B` on held-out scenario × seller cells, the recommended policy lowers completed price by **2.06** synthetic units and raises mean buyer surplus by **2.09**, while agreement falls by **8.4 percentage points** and mean rounds rise by **0.51**. That is why the repository keeps price, reliability and time-to-deal together.

## Results

Run `python scripts/rebuild_demo.py`. The current machine-readable outputs are:

```text
reports/model_metrics.json
reports/policy_kpis.json
reports/data_quality.json
reports/leakage_audit.json
reports/run_manifest.json
reports/multimodal_demo.json
reports/voice_demo.json
artifacts/monitoring/drift_report.json
```

The stakeholder version is in `STAKEHOLDER_MEMO.md`; the engineering details are in `TECHNICAL_REPORT.md`.

## What I would change with real marketplace data

The next step is not a more exotic model. It is real event-time data with actual inventory, location and seasonality; a warehouse-backed point-in-time feature layer; business-calibrated costs for failed trade and latency; controlled online evaluation; cohort calibration; and production ownership of the monitoring/rollback thresholds.

## Author

Layan Oraidi
