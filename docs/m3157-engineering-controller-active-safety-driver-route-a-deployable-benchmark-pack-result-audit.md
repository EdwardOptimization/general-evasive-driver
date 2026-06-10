# M3157 Route A Deployable Benchmark Pack Result Audit

## Summary

- status: completed
- audited artifact: `runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_materialization_preflight/summary.json`
- decision: `accept_m3156_benchmark_pack_route_to_m3158_validation_prep`
- M3156 status pass: true
- M3156 gate matrix pass: true
- required artifacts present: true
- benchmark metric rows: 18
- known failure taxonomy rows: 7
- contract guard rows: 13
- claim boundary rows: 23
- M3105 success/collision/offtrack/speed-too-low: 57/5/2/0
- M3153 action-channel-sensitive comparisons: 0/21
- next route: M3158 Route A deployable benchmark pack validation-prep plan.

## Artifact Audit

M3156 is accepted as a complete and claim-safe benchmark-pack materialization.
It packages the current M3105/M3103 active-safety reflex incumbent into a
Route A deployable evidence pack without changing the actor, running a new
environment, fitting a policy, replaying a rollout, ranking drivers, or
promoting a checkpoint.

The accepted pack contains:

- `deployable_driver_contract_snapshot.json`
- `deployable_benchmark_pack_manifest.json`
- `benchmark_metric_rows.csv`
- `known_failure_taxonomy_rows.csv`
- `contract_guard_rows.csv`
- `claim_boundary_rows.csv`
- `gate_matrix.csv`
- `summary.json`
- `docs/m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight.md`

The contract evidence is preserved:

- public runtime API: `ActiveSafetyReflexDriver.act(obs72)`
- input contract: actor-visible obs72 current-frame vector
- output contract: direct action3 `[steer, throttle, brake]`
- output semantics: `direct_action_clipped`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- hidden oracle actor input required: false
- TTC actor input required: false

## Benchmark Pack Evidence

The benchmark rows preserve the M3105 full-fresh denominator and incumbent
metrics:

- measurement episode rows: 64
- success count/rate: 57 / 0.890625
- collision count/rate: 5 / 0.078125
- offtrack count/rate: 2 / 0.03125
- speed-too-low count: 0
- clearance margin mean: 10.981307227309182
- high sideslip fraction mean: 0.057246427530285714
- lateral RMSE mean: 1.1406683690535837
- action clip fraction mean: 0.0
- raw action abs max: 1.0

The known-failure taxonomy is explicit rather than hidden:

- residual blockers: 7
- collision blockers: 5
- offtrack blockers: 2
- speed-too-low blockers: 0
- every blocker preserves the M3153 terminal-invariant negative replay label
- M3153 comparison rows: 21
- M3153 action-channel-sensitive comparisons: 0

## Interpretation

This audit accepts M3156 as the Route A deployable benchmark pack for the
current incumbent. The pack is useful because it centralizes the driver
contract, metric denominator, known residual failure taxonomy, negative replay
diagnostics, and claim-boundary guards that were previously spread across
M3105, M3139, M3153, M3154, and M3155 artifacts.

This audit does not accept M3156 as a validation result or performance verdict.
The correct reading is narrower:

- the M3105/M3103 incumbent is deployable through the public obs72-to-action3 API
- the incumbent is incomplete against the hard-safety objective
- the residual blockers are 5 collision and 2 offtrack rows on the 64-row fresh panel
- the local M3142/M3153 action-delta replay branch was negative on those seven rows
- future validation must start from this disclosed pack rather than from an unpackaged metric claim

## Rejected Claims

- validation result
- ranking or winner selection
- checkpoint promotion
- driver-performance verdict
- current-sim verdict
- robustness result
- high-fidelity validation result
- paper evidence
- finite-window-vs-GRU conclusion
- full ideal driver completion
- repair success
- feasibility proof
- level3 self-identification

## Decision

M3157 accepts M3156 as complete and claim-safe, and routes exactly one follow-up
to M3158 Route A deployable benchmark pack validation-prep planning.

M3158 must plan a bounded validation surface before any execution. It should
define validation denominators, same-case comparison requirements, failure
taxonomy coverage, runtime/reporting artifacts, and go/no-go gates while
preserving the obs72/action3 contract and the explicit residual blocker
disclosure.
