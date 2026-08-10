# Technical report

## Problem

Last Price began as a controlled bargaining experiment: keep the economic state fixed and change the buyer policy. This repository asks a different engineering question: can that experiment be turned into a production-style data-science system without contaminating evaluation with post-outcome information?

## Data contract

Rows are grouped by `scenario_id`. The production layer adds deterministic scenario-level context for time, location, product and inventory. Those fields are synthetic, but they are fixed within scenario and generated before model training.

## Targets

- `agreed`: conversion/reliability model on every negotiation.
- `price`: regression model only on completed negotiations.

Price and agreement remain separate because dropping failed trades can make an aggressive bargaining policy look artificially cheap.

## Split

Scenarios are sorted by timestamp. The newest 25% are held out. Entire scenarios move together, so treatment siblings never cross the split boundary.

## Features

Only pre-negotiation economic and market context enters the feature matrix. Outcome-derived variables are blacklisted and tested.

## Models

The project compares random forests against prior/median dummy baselines. This is intentionally conservative: a production demo should first prove that it beats a trivial rule and that its evaluation is valid before adding more complex models.

## Decision layer

Candidate buyer policies are scored using predicted agreement probability, predicted price conditional on trade, deadlock cost and expected negotiation time. The selected policy is evaluated on the held-out row corresponding to that scenario/seller/policy.

## Serving

FastAPI exposes health, agreement probability, conditional price and policy recommendation endpoints. Artifacts are serialized with joblib and can be served in Docker.

## Monitoring

A stress batch applies an inventory shock, stockout-risk increase, competitor repricing and city-composition shift. Feature and prediction drift metrics are generated as a machine-readable report.

## Scope

All numerical performance is on synthetic data. The repository demonstrates engineering and evaluation discipline, not live-market efficacy.
