# CV bullets — use only after you can explain the implementation

**Last Price — Marketplace ML & Algorithmic Bargaining Laboratory**

- Built a reproducible marketplace data-science pipeline spanning SQL analytics, point-in-time feature engineering, scenario-grouped temporal validation, model training, API serving and drift monitoring across 3,000 synthetic negotiations and 500 related economic scenarios.
- Evaluated agreement and conditional-price models on the newest 125 held-out scenarios (750 negotiations; zero scenario overlap): agreement ROC-AUC **0.789 vs 0.500 baseline** and price MAE **2.54 vs 23.72 baseline**.
- Designed a held-out policy-selection layer that jointly tracks price, buyer surplus, agreement and negotiation time; the selected policy lowered completed price by **2.06** synthetic units but reduced agreement by **8.4 pp**, making the business trade-off explicit rather than optimizing one metric blindly.
- Implemented model/data run manifests, dataset hashes, out-of-sample prediction logging, leakage audits, GitHub Actions, Dockerized FastAPI inference and synthetic drift stress tests.
- Added transcript-to-SQL query handling with an optional Whisper adapter and a deliberately scoped image/text/structured feature-fusion smoke benchmark.

**Do not claim:** production revenue impact, live-user deployment, real LLM negotiation results, or years of professional experience from this repository.
