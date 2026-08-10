# Last Price — Experiment 1 preregistration draft

## Question
Does assignment to a different negotiating model change the transaction price for economically identical buyers?

## Design
Fully crossed buyer-model × seller-model factorial design. Each repetition uses the same buyer valuation, seller cost, reference price, information set, bargaining protocol, maximum rounds, and prompt template. Treatment execution order is shuffled from a recorded master seed.

## Primary outcome
Transaction price conditional on agreement.

## Co-primary extensive-margin outcome
Agreement probability. Price and agreement must be reported together so a model cannot appear better merely by walking away more often.

## Primary estimand
`ABP(m) = E[P(m, s, r) - P(b0, s, r)]`, paired within seller-model `s` and repetition `r` whenever both negotiations agree.

## Cost-shock extension
Increase seller cost by a common preregistered percentage while leaving buyer valuation unchanged. Pair shocked and baseline cells and compute `experienced inflation = P(shock) / P(baseline) - 1`.

## Exclusions
API/network/provider failures are not negotiation failures. Turn-limit failures remain valid `agreed=false` outcomes. No cell is dropped because its result is inconvenient.

## Freeze rule
Commit this protocol and configuration before the first real-model batch used for inference.
