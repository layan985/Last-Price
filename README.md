# Last Price

What happens when two economically identical buyers are represented by different negotiating agents?

Last Price started as a controlled bargaining experiment. I kept the economics layer, then built a second layer around it to practice the work expected in analyst and junior data-science roles: generating and validating a dataset, querying it in SQL, building KPIs, segmenting performance, training predictive baselines, checking leakage, and presenting results in a dashboard and Excel workbook.

The agents included here are **mechanical test policies**. Results from them are synthetic validation results, not evidence about GPT, Claude, Gemini, or any other real model.

## What is in the repo

### Experimental layer
- alternating-offer bargaining engine
- controlled buyer × seller treatment cells
- deterministic seeds and reproducible runs
- transcript logging
- transaction-price and surplus accounting
- matched buyer-model effects with bootstrap intervals
- buyer/seller/interaction variance decomposition
- paired seller-cost shock experiment
- preregistration draft for later real-model experiments

### Analytics / data-science layer
- 3,000-row synthetic portfolio dataset across 500 economic scenarios
- Python data-quality checks
- SQLite database and analyst-friendly views
- SQL query pack using CTEs, joins, conditional aggregation, and window functions
- KPI and segmented performance analysis
- grouped train/test splitting by `scenario_id` to prevent treatment leakage
- baseline and random-forest regression/classification models
- MAE, RMSE, R², accuracy, F1, ROC-AUC, and permutation importance
- Jupyter case-study notebook
- Streamlit dashboard
- Excel dashboard with formulas and analysis-ready raw data
- automated tests and GitHub Actions CI

## Synthetic portfolio result

The purpose of the synthetic run is to verify the workflow, not to establish a substantive result about AI models.

| Buyer policy | Agreement rate | Mean completed price | Mean buyer surplus | Mean rounds |
|---|---:|---:|---:|---:|
| buyer_A | 57.2% | 101.65 | 18.02 | 4.49 |
| buyer_B | 73.7% | 108.66 | 17.05 | 3.76 |
| buyer_C | 84.4% | 114.21 | 14.03 | 3.03 |

The useful analyst finding is the trade-off: the lowest-price policy also has the lowest completion rate and takes longer. Reporting only average price would therefore give a misleading recommendation.

Grouped test split:

| Task | Model | Main test metric |
|---|---|---:|
| Price regression | Median baseline | MAE 24.92 |
| Price regression | Random forest | MAE 2.19 |
| Agreement classification | Majority baseline | ROC-AUC 0.50 |
| Agreement classification | Random forest | ROC-AUC 0.78 |

The very high price-model R² is expected in a deterministic simulator where the target is mechanically related to the economic inputs. It is useful as a pipeline check, not evidence that the model will generalize to real transaction data.

## Run it

```bash
python -m pip install -e ".[analytics,dev]"
lastprice identity --repetitions 200
lastprice inflation --repetitions 200 --shock 0.10
lastprice portfolio --scenarios 500 --out results
pytest -q
streamlit run dashboard/app.py
```

## Analyst artifacts
- `sql/analysis_queries.sql` — SQL analyses and QA checks
- `notebooks/01_analyst_data_science_case.ipynb` — end-to-end case study
- `dashboard/app.py` — interactive dashboard
- `PORTFOLIO.md` — employer-facing skill map
- `INTERVIEW_NOTES.md` — technical questions to defend before putting the project on a CV

## Experimental sequence
1. Identity swap — hold the economy fixed; randomize model identity.
2. Seller-model swap — isolate seller-side effects.
3. Cost shock — measure model-specific price pass-through.
4. Information treatments — vary access to market information.
5. Market structure — add competition, search, inventory constraints, and repeated interaction.
6. Replace mechanical policies with real model adapters only after the protocol is frozen.

See `METHODOLOGY.md` and `experiments/PREREGISTRATION_V1.md` for the research design.
