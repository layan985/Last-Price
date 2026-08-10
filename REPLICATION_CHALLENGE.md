# Independent Replication Challenge

Last Price is designed so another person can reproduce the shipped synthetic experiment without receiving generated model binaries, processed datasets, or a database from the author.

## Goal

Starting from a fresh clone, verify whether the repository regenerates the same experimental structure, passes the data-quality and leakage gates, and produces materially matching held-out model and policy results.

## Reproduce

```bash
git clone https://github.com/layan985/Last-Price.git
cd Last-Price
python -m pip install -e ".[dev]"
python scripts/rebuild_demo.py
pytest
ruff check src tests scripts
```

## What to report

Please record:

- operating system and Python version
- commit SHA
- whether the rebuild completed
- whether the data-quality gate passed
- whether the leakage audit passed
- train/test scenario overlap
- test count and status
- agreement ROC-AUC and Brier score
- price RMSE and MAE
- policy KPI differences versus the fixed baseline
- any discrepancy, warning, or undocumented step required

## Outcome categories

**Exact reproduction:** deterministic outputs match exactly where the environment is pinned and exact equality is expected.

**Substantive reproduction:** small numerical differences exist but the same data split, validation gates, ranking, and substantive conclusions are recovered.

**Discrepancy:** a documented result cannot be reproduced, a gate fails, or additional undocumented information is required.

All three outcomes are useful. A discrepancy should not be hidden or converted into a successful result.

## Evidence

Open a GitHub issue with the command output or a link to an independent fork/commit. The independent-reproduction count remains zero until a third party provides a public record.

## Scope

This challenge validates reproducibility of the synthetic portfolio system. It does not validate real-market performance, causal claims about commercial LLMs, or production experience.