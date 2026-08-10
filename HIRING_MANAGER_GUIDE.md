# Last Price in five minutes

This is the shortest path through the repository for a hiring manager or interviewer.

## 1. Start with the decision, not the architecture

The held-out policy selector lowers completed price by **2.06 synthetic units** and raises mean buyer surplus by **2.09**, but agreement falls by **8.4 percentage points** and negotiations take **0.51 more rounds** on average.

That trade-off is the point: optimizing one KPI would produce a bad marketplace recommendation.

See: `STAKEHOLDER_MEMO.md` and `reports/policy_kpis.json`.

## 2. Check whether the models beat simple baselines

The newest 125 scenarios are held out as the test period, giving 750 negotiations with zero scenario overlap.

| Task | Baseline | Model |
| --- | ---: | ---: |
| Agreement ROC-AUC | 0.500 | 0.789 |
| Agreement Brier | 0.196 | 0.164 |
| Price MAE | 23.72 | 2.54 |
| Price RMSE | 28.79 | 3.33 |

See: `reports/model_metrics.json` and `TECHNICAL_REPORT.md`.

## 3. Inspect the leakage boundary

Treatment rows sharing one `scenario_id` are kept together. The training matrix rejects post-outcome fields such as price, agreement, negotiation rounds and realized surplus.

See: `reports/leakage_audit.json`, the feature-contract code under `src/`, and the tests.

## 4. Inspect SQL rather than trusting a skill label

The `sql/` folder contains marketplace KPI, segmentation, inventory, window-function and model-monitoring queries. The SQLite layer stores negotiations, model runs and out-of-sample predictions.

## 5. Inspect the engineering path

The repo includes:

- FastAPI inference;
- Docker packaging;
- model/data run manifests;
- prediction logging;
- dataset SHA-256 fingerprints;
- drift stress tests;
- GitHub Actions rebuild/tests/lint.

See `MLOPS.md` and `Dockerfile`.

## Questions I should be able to answer without notes

1. Why is random row splitting invalid here?
2. Why is conditional price alone a dangerous policy objective?
3. What is leakage in this experiment?
4. Why keep a dummy baseline when the model score looks strong?
5. What would change with real marketplace event data?
6. Which production alerts would trigger retraining versus rollback?

## Scope

The shipped negotiations are synthetic mechanical-policy data. This repository does **not** establish production revenue impact, live-user deployment, real LLM bargaining effects or years of professional experience.