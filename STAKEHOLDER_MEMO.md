# Last Price — marketplace policy pilot memo

## Decision

Do **not** promote the current policy optimizer to a live marketplace. Use it as a simulation-backed pilot candidate and as the template for a real-data experiment.

## What the held-out test says

The newest 125 scenarios are held out as a complete time block. No scenario appears in both training and test.

Against the fixed `buyer_B` reference on 250 held-out scenario × seller decisions, the optimizer produces:

| KPI | Baseline | Recommended | Change |
|---|---:|---:|---:|
| Agreement rate | 77.6% | 69.2% | -8.4 pp |
| Mean completed price | 102.58 | 100.52 | -2.06 |
| Mean buyer surplus | 12.93 | 15.02 | +2.09 |
| Mean rounds | 5.90 | 6.41 | +0.51 |
| Composite realized utility | 9.070 | 10.315 | +1.245 |

The model finds cheaper outcomes, but some of the gain comes with lower trade completion. That is exactly the failure mode the original research design warns about: a hard-bargaining policy can look good on conditional price if failed trades disappear from the dashboard.

## Model quality

The agreement model reaches ROC-AUC **0.789** against a **0.500** prior baseline. The conditional-price model reaches RMSE **3.33** against **28.79** for the median baseline. These numbers are from synthetic data and should be read as a pipeline validation result, not as a live-market performance claim.

## Guardrails before any real launch

A real pilot needs logged marketplace events, point-in-time inventory and pricing data, explicit customer-welfare constraints, calibration by product/location cohort, a randomized holdout, rollback thresholds, privacy review, and monitoring for seasonality, inventory mix and competitor-price shifts.

The synthetic results in `reports/policy_kpis.json` test the machinery. They do not establish production uplift.
