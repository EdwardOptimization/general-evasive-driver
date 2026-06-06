# M2959 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_m2960_actor_head_delta_bounded_execution_preflight`
- manifest: `experiments/manifests/m2959-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-design.json`
- parent synthesis: `docs/m2958-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-admission-branch-synthesis.md`
- parent audit: `docs/m2957-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-result-audit.md`
- parent summary: `runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/summary.json`
- parent candidate rows: `runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_head_delta_execution_admission_candidate_rows.csv`
- follow-up manifest: `experiments/manifests/m2960-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-preflight.json`
- next: `m2960-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-preflight`

## Design Decision

M2959 admits exactly one next route:

```text
m2960-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-preflight
```

M2959 is design-only. It does not reset, step, roll out, replay, validate, train, run PPO, rank, promote, mutate checkpoints, execute dependency work, probe an adapter, select a winner, compute a success-rate verdict, or claim implementation readiness, repair success, driver performance, paper evidence, current-sim verdict, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

## Execution Surface

M2960 may consume only the accepted actor-head delta admission chain:

```text
docs/m2958-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-admission-branch-synthesis.md
docs/m2957-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-result-audit.md
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/summary.json
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_head_delta_execution_admission_candidate_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_head_delta_execution_admission_rejection_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/source_guardrail_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/actor_delta_contract_guard_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight/gate_matrix.csv
```

The bounded execution candidate set is exactly the 56 M2956 rows with:

```text
execution_admission_status: actor_head_delta_execution_admission_materialized_for_separate_bounded_execution_design
ordinary_engineering_denominator_allowed_after_audit: true
validation_denominator_allowed: false
paper_denominator_allowed: false
high_fidelity_readiness_allowed: false
self_id_claim_allowed: false
actor observation/action: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
route/source/evaluator/diagnostic/progress/verdict labels actor-visible: false
```

Source distribution inherited from M2916:

```text
M2737 source-diverse closed-loop diagnostic rows: 18
M2746 source-diverse failure-taxonomy scenario-role rows: 14
M2807 post-clearance non-same cross-axis rows: 12
M2816 recoverability-window instrumented rows: 12
```

M2960 must not execute the 11 blocked stale fixed-source rows. Those rows remain rejection and guardrail context only.

## Resolution Rules

M2960 must write execution-candidate and execution-resolution artifacts before any reset or step. For each of the 56 admitted rows, resolution must preserve:

```text
actor_head_delta_candidate_id
source_execution_admission_candidate_id
source_milestone
source_row_id
source_family
task_family
workload_id
task_source_id
profile_name
parent_checkpoint_path
parent_profile_config_path
actor_head_delta_panel_spec_ids
actor_head_delta_traceability_count
actor 72/action 3
claim boundary flags
```

Resolution rejects or records a failure row if:

```text
the row is not admitted by M2956
the row belongs to the 11 stale fixed-source blocked rows
parent_checkpoint_path or parent_profile_config_path is missing
the executable workload row cannot be resolved from workload_id/task_source_id/profile_name
actor input contract would change
hidden/oracle/future-target actor input is required
route/source/evaluator/diagnostic/success/progress/verdict labels would become actor-visible
the row would enter validation paper high-fidelity promotion or self-ID denominators
the actor-head delta wrapper cannot preserve zero-delta parent identity and residual bounds
```

It must not substitute another row, source family, task family, profile, checkpoint, or repair overlay.

## Execution Protocol

M2960 may execute reset, step, policy action, and rollout only for resolved M2956 admitted rows. It must execute at most one diagnostic rollout per row.

Default eval seed namespace:

```text
eval_seed = 296000 + row_index
```

Allowed read-only side effects:

```text
load parent checkpoint read-only for resolved candidates
instantiate actor-head delta scaffold or equivalent bounded residual wrapper
run current-sim diagnostic rollout for resolved candidates
write bounded execution artifacts
```

Required actor-head delta execution constraints:

```text
parent actor action remains the base action path
residual delta is bounded before action combination
combined action is clipped to deployed action range
zero-delta identity is recorded as the initialization/contract baseline
no evaluator labels hidden dynamics oracle labels future targets progress labels or verdict labels are actor inputs
```

Forbidden in M2960:

```text
checkpoint mutation, save, rank, or promotion
training, PPO, replay, or private holdout
measured validation
source build or dependency execution
adapter probe or external simulation
profile-specific tuning
active config overwrite
repair overlay beyond the admitted actor-head delta wrapper
source-family, task-family, profile, checkpoint, controller, or candidate ranking
winner selection
success-rate verdict computation
```

M2960 may record diagnostic closed-loop metrics such as termination reason, collision, off-track, obstacle completion, clearance, episode length, return, finite metric checks, residual-delta summary fields, and bounded row lineage. These fields remain diagnostic only.

## Output Artifacts

M2960 should write:

```text
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/summary.json
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/execution_candidate_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/execution_resolution_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/actor_head_delta_contract_execution_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/bounded_execution_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/bounded_execution_failure_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/source_milestone_aggregate.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/task_family_aggregate.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/guardrail_context_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/actor_contract_guard_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/claim_boundary_rows.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/gate_matrix.csv
runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight/run_state.json
docs/m2960-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-preflight.md
experiments/manifests/m2961-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-result-audit.json
```

## Gate Matrix

M2960 passes only if all of these hold:

```text
M2959 design exists
M2958 synthesis continues to M2959/M2960 route
M2957 accepts M2956
M2956 summary status_pass true
M2956 gate_matrix_pass true
56 admitted actor-head delta rows loaded
11 blocked stale rows loaded and not executed
56 admitted rows resolved or explicitly accounted by failure rows
only M2956 admitted rows are execution candidates
actor-head delta contract execution rows are written
actor 72/action 3 preserved
hidden_oracle_actor_input_required false
future_target_actor_input_required false
actor input changed false
route/source/evaluator/diagnostic/success/progress/verdict labels actor-visible false
checkpoint mutation/save/rank/promotion false
profile_specific_tuning false
active_config_overwritten false
dependency_execution_performed false
replay validation training PPO private holdout false
ranking_run false
winner_selected false
success_rate_verdict_claim_made false
driver_performance_claim_made false
validation_readiness_claim_made false
paper_claim_made false
high_fidelity_claim_made false
self_id_claim_made false
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every admitted row is accounted for and all claim, actor, checkpoint, and guardrail boundaries are clean. A pass does not mean the driver succeeded.

## Follow-Up

M2959 admits:

```text
m2960-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-preflight
```

M2960 must register M2961 result audit before any interpretation.

## Claim Boundary

Allowed M2959 claim:

```text
M2959 defines an actor-safe bounded diagnostic execution protocol for the accepted M2956 actor-head delta admission surface and admits one separately pre-registered execution preflight.
```

Rejected claims:

```text
execution result
implementation readiness
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
task-family ranking
profile ranking
candidate ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
