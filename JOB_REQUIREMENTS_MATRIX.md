# Job requirement coverage

This file maps the target data-science job description to concrete evidence in this repository.

| Requirement | Evidence here | What it proves / does not prove |
|---|---|---|
| Applied data science / ML | Agreement classifier, conditional-price regressor, held-out policy selection, KPI report | Proves end-to-end applied modeling on synthetic marketplace data; does **not** create 4–8 years of employment |
| SQL & Python | `src/last_price/`, analytical SQLite DB, six SQL analyses with CTEs/windows/joins/aggregations | Demonstrates Python + relational analysis and reproducible data pipelines |
| Pandas / NumPy / scikit-learn | deterministic enrichment, validation, preprocessing, RF models, metrics | Direct implementation evidence |
| Reliable pipelines | one-command rebuild, data-quality gates, schema checks, dataset SHA-256 | Demonstrates reproducibility and validation discipline |
| MLOps fundamentals | serialized artifacts, run registry, prediction log, GitHub Actions, Docker, FastAPI | Production-style lifecycle; not a claim of operating a commercial service |
| Observability | PSI, Jensen-Shannon drift, prediction drift, synthetic stress batch | Demonstrates drift detection and alerting |
| Leakage risk | post-outcome feature blacklist + grouped temporal split + tests | Strong evidence of point-in-time evaluation discipline |
| Market dynamics | time, city, product, inventory, stockout risk, competitor quote, season | Demonstrates modeling structure; these portfolio context variables are synthetic |
| Communication & ownership | `STAKEHOLDER_MEMO.md`, `TECHNICAL_REPORT.md`, README, interview notes | Shows ability to explain decisions/tradeoffs at different levels |
| Software engineering | package layout, typing, tests, CLI, API, CI, Docker | Direct engineering evidence |
| Multimodal / vision | image + text + structured fusion benchmark | Synthetic smoke benchmark only; not real-world CV expertise |
| Voice AI | transcript→intent→parameterized SQL + optional Whisper adapter | ASR/NLU exposure; Whisper path requires optional dependency |
| Bachelor’s in STEM | Not satisfied by repository work | Must be represented honestly on applications |

## What to say in an interview

The strongest claim is:

> “I built a production-style marketplace ML system around a bargaining experiment. I separated conversion from conditional price, enforced a point-in-time feature boundary, used a scenario-grouped temporal holdout to prevent leakage, logged reproducible model runs, served the models behind an API, and stress-tested drift. The data are synthetic, so I treat the project as engineering and evaluation evidence rather than production-impact evidence.”

Do not convert project months into fake years of experience.
