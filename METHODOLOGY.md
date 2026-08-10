# Methodology

## Core estimand

Last Price asks whether changing only the model representing an otherwise identical economic actor changes transaction outcomes.

The first design is a fully crossed randomized factorial experiment. For repetition `r`, the economic state is fixed. Buyer model and seller model are treatment assignments. The primary estimand is the average difference in transaction price caused by assignment to buyer model `m`, relative to a preregistered baseline, averaging over seller-model assignments.

`ABP_m = E[P | buyer=m] - E[P | buyer=baseline]`

## Identification discipline

Real-model runs should hold constant: model prompt, economic primitives, information available to the role, token/turn budget, API settings except model identity, stopping rules, and experiment code version. Treatment order should be randomized. Model/version identifiers and provider timestamps should be recorded. Failed API calls are infrastructure failures, not negotiation failures.

## Inflation experiment

Each treatment cell is rerun under a seller-cost shock while preserving buyer valuation and experimental rules. For paired successful transactions:

`experienced_inflation_i = P_i(shock) / P_i(baseline) - 1`

## Scope

The included mechanical policies are test fixtures. They validate randomization, bargaining logic, event logging, pairing, and estimand computation. They are not evidence about any real language model provider.
