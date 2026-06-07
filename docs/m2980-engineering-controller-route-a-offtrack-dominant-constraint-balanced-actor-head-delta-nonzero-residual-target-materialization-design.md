# M2980 Engineering Controller Route A Actor-Head Delta Nonzero Residual Target Materialization Design

## Metadata

- status: completed
- decision: `admit_m2981_residual_target_source_feasibility_preflight`
- manifest: `experiments/manifests/m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-materialization-design.json`
- parent design: `docs/m2979-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.md`
- parent trace capture: `runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-source-feasibility-preflight.json`
- next: `m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-source-feasibility-preflight`

## Design Decision

M2980 admits one bounded target-source feasibility preflight.

Formal decision:

```text
admit_m2981_residual_target_source_feasibility_preflight
```

M2979 correctly rejects direct residual fitting because M2977 raw traces and
M2966/M2970 objective/admission rows do not contain numeric residual deltas or
teacher actions. M2980 does not materialize targets. It defines the smallest
next evidence step: a no-fitting feasibility/materialization preflight that
tests whether actor-safe target rows can be produced from the accepted raw
trace surface and trainer-side local-action search contract.

The design follows the existing repository pattern used by target-panel and
local-recovery target work: the simulator or replay search may be used only as
a trainer-side target selector, while target labels, target provenance, hidden
diagnostics, and outcome verdicts must remain outside actor inputs.

## Source Contract

M2981 must consume:

```text
M2977 raw actor-view trace index and raw trace files
M2977 raw trace guard and availability rows
M2970 training-admission candidate and guard rows
M2970 objective-balance rows
M2966 objective component and row-assignment rows
M2979 fitting-admission design
```

The source counts are fixed:

```text
future training candidates: 43
success identity guards: 13
stale guardrails: 11
raw actor-view traces: 56
actor observation/action: 72/action 3
```

M2981 must preserve this accounting and fail closed if any join is incomplete.

## Target Semantics

M2981 may materialize target-source feasibility rows for three future training
families:

```text
collision_clearance_residual_objective
offtrack_recovery_residual_objective
speed_floor_context_guard_objective
```

For each admitted future training row, the target source must be a bounded
trainer-side local-action search around the recorded base action from M2977.
The preflight must record the search contract, candidate deltas, acceptance
metric, and selected target provenance. It must not use future target labels or
objective labels as actor inputs.

Required target tensor contract if a target is admitted:

```text
target_action_delta: float32 [T, 3]
target_valid_mask: bool [T]
target_loss_weight: float32 [T]
target_family: metadata only, actor-invisible
target_source_provenance: metadata only, actor-invisible
```

The target may be sparse. If only one recovery step is selected, the mask must
be true only at that step and false elsewhere.

## Guard Contract

Success identity rows are guard rows, not positive residual targets:

```text
success identity target_action_delta: zero only
success identity target_valid_mask: guard-only
success identity positive target: false
```

Stale fixed-source guardrails remain excluded:

```text
stale guardrail executed: false
stale guardrail target materialized: false
stale guardrail training denominator: false
stale guardrail validation/paper denominator: false
```

M2981 must write separate rows for candidate targets, success-identity zero
guards, and stale guardrail exclusions.

## Required M2981 Artifacts

M2981 must write:

```text
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/summary.json
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/target_source_plan_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/target_candidate_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/success_identity_zero_target_guard_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/stale_guardrail_exclusion_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/actor_contract_guard_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/claim_boundary_rows.csv
runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight/gate_matrix.csv
docs/m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-source-feasibility-preflight.md
```

If M2981 cannot materialize target tensor files without violating the contract,
it must still preserve feasibility rows and fail closed rather than inventing
targets.

## Gates

M2981 must pass these gates:

```text
source artifacts present: true
raw trace joins complete: true
future training candidates accounted: 43
success identity guards accounted: 13
stale guardrails accounted: 11
actor observation/action: 72/action 3
target labels actor-visible: false
target provenance actor-visible: false
hidden/oracle/future-target actor input: false
success identity positive targets: 0
stale guardrail target materializations: 0
residual fitting/training/validation/ranking/promotion: false
repair-success/performance/paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID claims: false
```

## Supported Claims

M2980 supports only:

```text
M2980 defines the target-source feasibility/materialization contract needed
before residual fitting can be considered.

M2981 is the next admissible evidence step.
```

M2980 does not claim that targets already exist or that residual fitting is
ready.

## Rejected Claims

M2980 rejects:

```text
target tensors materialized in M2980: false
residual fitting admitted directly: false
training/validation/ranking/promotion admitted directly: false
repair success or driver performance established: false
paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## Boundary

M2980 is design-only. It does not run target search, write target tensors, fit
residuals, train, validate, rank, promote, mutate checkpoints, or claim driver
performance. The next milestone must implement the smallest preflight that can
test target-source feasibility while preserving actor and claim boundaries.
