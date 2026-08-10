# MLOps design

A rebuild is one command:

```bash
make rebuild
```

The rebuild:

1. regenerates deterministic market context,
2. runs data-quality and leakage audits,
3. creates the analytical SQLite database,
4. trains agreement and conditional-price models,
5. writes a dataset SHA-256 fingerprint,
6. records a run manifest and model metrics,
7. stores out-of-sample predictions,
8. evaluates the policy layer,
9. runs a synthetic drift stress test,
10. executes voice-query and multimodal smoke benchmarks.

`model_runs` stores the dataset hash, time, git commit when available, and metrics. `model_predictions` links out-of-sample predictions back to treatment IDs.

The repo uses GitHub Actions for rebuild + tests + linting. The Docker image serves the same serialized model artifacts through FastAPI.

## Monitoring

The demo monitor checks numeric PSI, categorical Jensen-Shannon divergence and agreement-prediction drift. The stress batch deliberately reduces inventory, raises stockout risk and competitor quotes, and shifts city composition. An alert is expected; silence would be a failed monitor test.

## Optional production tooling

The `mlops` extra reserves integrations for MLflow and Evidently. The core project deliberately does not require either dependency to reproduce the registry and drift logic.
