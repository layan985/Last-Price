# Interview notes

Be able to explain these without reading the README.

## Why split on scenario rather than row?

All buyer × seller treatments inside a scenario share the same economic state. A row split would leak that state into both training and test sets. The holdout therefore moves complete scenarios together and uses the newest scenarios as test data.

## Which fields are banned?

Realized price, agreement, rounds, buyer/seller surplus, total surplus, capture rates and price-relative-to-reference are post-outcome fields. They are never fed into the models.

## Why keep price and agreement separate?

A policy can look cheap by refusing difficult trades. Price is evaluated conditional on completed trades, while agreement is modeled on all negotiations.

## Why doesn't a high R² prove much here?

The data are synthetic and the economic primitives that generate price are available to the model. The point of the project is the evaluation boundary, deployment plumbing and decision tradeoff, not claiming that synthetic predictability transfers to a live marketplace.

## What does the policy optimizer do?

For each scenario and seller, it scores candidate buyer policies using predicted probability of agreement, predicted price conditional on agreement, a deadlock penalty and a time cost based on historical rounds. The recommended policy is then evaluated on held-out realized outcomes.

## How is drift detected?

The demo compares training-distribution features with a stress batch using PSI for numeric variables and Jensen-Shannon divergence for categorical variables, plus drift in the model's agreement probabilities.

## What would change with real data?

The feature contract would be driven by the actual event schema and point-in-time availability. The database would move to a production warehouse, calibration would be monitored by cohort, model registry/observability could be delegated to MLflow/Evidently or cloud-native services, and the KPI objective would be set with business owners.
