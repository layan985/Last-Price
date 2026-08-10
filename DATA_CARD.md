# Data card

The repository deterministically generates a **synthetic** negotiation dataset from the Last Price mechanical-policy experiment using a fixed seed. It is a portfolio and methods dataset, not a record of real consumers, firms, or commercial language-model behavior.

## Unit

One row is one buyer-policy × seller-policy negotiation inside a fixed economic scenario.

## Core fields

Economic primitives include buyer value, seller cost, reference price, gains from trade and a cost-shock indicator. Outcomes include agreement, transaction price, negotiation rounds and realized surplus.

The production-ML layer adds deterministic scenario-level context: timestamp, city, product ID, inventory, stockout risk and competitor quote. These additions are synthetic and are generated only from `scenario_id` plus a fixed seed. They are held constant across treatments inside a scenario.

## Leakage boundary

Training features are limited to fields that could be known before the negotiation. Realized price, agreement, rounds, surplus and capture-rate fields are explicitly blacklisted as model inputs.

## Intended use

- SQL and analytics demonstrations
- leakage-safe model evaluation
- deployment and monitoring exercises
- policy-selection simulations

Do not cite model accuracy from this dataset as evidence about real marketplace performance.
