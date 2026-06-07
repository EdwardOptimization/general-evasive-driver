# M3024 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target-Source Feasibility Admission Design

## Metadata

- status: completed
- decision: `admit_m3025_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight`
- manifest: `experiments/manifests/m3024-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-admission-design.json`
- parent audit: `docs/m3023-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-result-audit.md`
- parent objective contract: `runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-preflight.json`
- next: `m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-preflight`

## Design Decision

M3024 admits exactly one no-execution target-source readiness/feasibility
materialization preflight.

Formal decision:

```text
admit_m3025_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight
```

The next milestone must not assume target-source feasibility. It must
materialize an auditable readiness panel that can either establish a legal
trainer-side target-source route or fail closed with explicit blocker rows.
This preserves the M3023 audit boundary: M3022 is an accepted objective
contract, not target-source feasibility, numeric target materialization,
fitting readiness, residual fitting, training, validation, ranking, promotion,
driver-performance evidence, paper evidence, current-sim verdict,
high-fidelity evidence, finite-window-vs-GRU evidence, full-driver completion,
or self-ID evidence.

## Route Constraint

The post-M2470 route plan keeps Route A focused on engineering-controller
progress under the deployable actor contract. It also warns against allowing
static process artifacts to become the main loop. M3024 therefore selects a
bounded infrastructure preflight only because it can answer a concrete
admission question that M3023 left unresolved:

```text
Can every M3022 objective row be traced to a legal trainer-side target-source
readiness state without changing actor inputs or pretending that summary-only
episode metrics are raw actor-view traces?
```

If the answer is negative, M3025 must preserve the blocker and route to audit,
trace-capture admission, branch synthesis, or stop. It must not continue to
target tensors.

## Source Evidence

M3023 accepts M3022 only as objective-contract materialization. The accepted
M3022 accounting is:

```text
row assignments: 32
profile/source guard rows: 32
actor contract guard rows: 8
claim boundary rows: 32
actor observation/action: 72/action 3
```

Objective rows split as:

```text
offtrack_recovery_broad_failure_contract: 22
collision_clearance_guard_contract: 5
speed_floor_guard_contract: 2
success_identity_context_guard: 3
```

Target-role admission must preserve:

```text
future target eligible failure/context rows: 29
success identity zero-target guard rows: 3
success_context future target rows: 0
candidate profile rows: 16
parent profile rows: 16
```

The important negative fact is that the M3015/M3018/M3022 chain contains
diagnostic episode summaries and localization rows, but not persisted raw
actor-view observation/action/response traces like the M2977/M2981 chain used.
Episode summary metrics such as return, mean reward, clearance, speed, and
off-track time are not legal target-source traces.

## M3025 Contract

M3025 must consume:

```text
M3022 objective-family, row-assignment, profile/source guard, actor guard,
claim-boundary, gate, and summary artifacts
M3023 result audit
M3024 design artifact
M3018 failure-localization rows and profile/source aggregate rows
M3015 diagnostic episode rows and execution guard rows
```

M3025 must write:

```text
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/summary.json
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/target_source_readiness_rows.csv
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/target_source_blocker_rows.csv
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/success_identity_guard_rows.csv
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/actor_contract_guard_rows.csv
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/claim_boundary_rows.csv
runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight/gate_matrix.csv
docs/m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-preflight.md
```

The readiness rows must account for all 32 M3022 row assignments. They must
separate future target-eligible failure/context rows from success identity
guards and must preserve the original profile, task_source, objective family,
failure family, source episode row index, and actor contract metadata.

For each of the 29 future target-eligible rows, M3025 may record only these
trainer/evaluator-side readiness states:

```text
episode_summary_available
raw_actor_view_trace_required
raw_actor_view_trace_available
target_source_feasibility_established
local_action_search_required_before_numeric_target
local_action_search_run
numeric_target_tensor_materialized
```

If no raw actor-view trace artifact exists for a row, the row must be marked
blocked for target-source feasibility. It must not be dropped or converted into
a target from scalar diagnostics.

For each of the three success identity rows, M3025 must write guard rows only:

```text
success_identity_zero_target_guard: true
positive_target_candidate: false
future_target_materialization_allowed: false
```

## Required Gates

M3025 must pass only as a claim-safe materialization/auditability preflight.
Its gates are:

```text
M3022/M3023/M3024 source artifacts present: true
all 32 row assignments accounted: true
future target-eligible rows accounted: 29
success identity zero-target guards accounted: 3
collision, speed-floor, offtrack, and success-context families preserved: true
raw actor-view trace availability reported for every future target row: true
summary-only episode metrics not accepted as raw traces: true
target-source feasibility established count may be 0
numeric target tensor materialized count: 0
local action search run: false
fitting/training/execution/validation/ranking/promotion run: false
actor observation/action: 72/action 3
hidden/oracle/future-target/source/route/outcome/objective/progress/verdict/TTC actor input: false
driver-performance/paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID claim: false
follow-up result-audit manifest registered: true
```

A zero-feasible result is allowed if and only if the blocker rows are explicit
and the target-source boundary is preserved. That outcome would be negative
readiness evidence, not failure to execute M3025.

## Forbidden Routes

M3025 must not:

```text
run environment reset, step, rollout, replay, validation, training, or PPO
run local-action search
materialize numeric target tensors, residual deltas, masks, weights, fitted artifacts, or checkpoints
turn episode summary metrics into raw traces or teacher actions
turn success_context rows into positive targets
drop collision clearance, speed-floor, parent-profile, candidate-profile, or weak-negative rows
change actor input/action shape or expose source/objective/outcome/progress/verdict labels to the actor
claim target-source feasibility beyond the rows that have legal trace evidence
claim validation, repair success, driver performance, paper evidence, current-sim verdict, high-fidelity evidence, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence
```

## Supported Claims

M3024 supports only:

```text
M3025 is the next admissible no-execution readiness/feasibility materialization preflight.
M3025 must preserve the M3022 32-row denominator and objective-family guard context.
M3025 must fail closed when raw actor-view traces are missing.
M3024 itself does not establish target-source feasibility or target materialization.
```

## Rejected Claims

M3024 rejects:

```text
M3022/M3023 established target-source feasibility: false
M3024 materialized target-source feasibility: false
M3024 materialized numeric targets: false
M3024 admitted fitting, training, validation, ranking, promotion, or checkpoint mutation: false
M3024 proved repair success, driver performance, paper evidence, current-sim verdict, high-fidelity evidence, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence: false
```

## Next Route

M3024 selects exactly one next route:

```text
m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-preflight
```

The next milestone is infrastructure. It may materialize readiness and blocker
artifacts only. It must route to a result audit before any interpretation or
continuation.
