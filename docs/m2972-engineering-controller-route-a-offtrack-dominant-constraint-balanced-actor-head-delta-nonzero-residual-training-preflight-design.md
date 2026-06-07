# M2972 Engineering Controller Route A Actor-Head Delta Nonzero Residual Training Preflight Design

## Metadata

- status: completed
- decision: `admit_m2973_nonzero_residual_training_trace_panel_preflight`
- manifest: `experiments/manifests/m2972-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-preflight-design.json`
- parent audit: `docs/m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-result-audit.md`
- parent materialization: `runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight.json`
- next: `m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight`

## Design Decision

M2972 admits exactly one next route:

```text
m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight
```

M2972 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, rank, promote, mutate checkpoints, execute dependency work,
select a winner, compute a success-rate verdict, or claim implementation
readiness, repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity readiness, full-driver completion, finite-window-vs-GRU
evidence, or self-ID evidence.

The next route is not residual fitting yet. It is a bounded trace-panel
preflight that must produce a deployable observation/action/response data
surface for later residual training. The reason is concrete: M2970 materialized
candidate metadata, but it did not contain raw deployable observation/action
traces. Training a residual head from metadata alone would be a false training
readiness claim.

## Route-Plan Alignment

`docs/post-m2470-route-plan.md` says Route A should move toward a usable
actuator-level controller baseline while preserving the human-view actor
contract. M2972 follows that route by moving from static candidate accounting
to a bounded data-panel preflight:

```text
allowed Route A direction:
  deployable actuator-level RL using ego response, actuator state, previous
  commands, and scene geometry

forbidden shortcut:
  hidden dynamics, oracle labels, slip/tire-force shortcuts, TTC, reference
  trajectory, precomputed success/progress signals, or controller labels in the
  actor input
```

M2973 may collect or export deployable trace data. It may not use that trace
data to validate performance, rank candidates, promote a checkpoint, or claim
paper/self-ID evidence.

## Accepted Input Surface

M2972 consumes the accepted M2970/M2971 chain:

```text
M2970 status_pass: true
M2970 gate_matrix_pass: true
source row assignments: 56
training-admission profile rows: 1
training-admission candidate rows: 43
training-admission guard rows: 24
objective-balance rows: 4
success identity guard rows: 13
stale guardrail rows: 11
actor contract guard rows: 18
claim boundary rows: 33
gate rows: 22
```

The M2973 trace-panel preflight must account for:

```text
future training candidates:
  offtrack_recovery_residual_objective: 35
  collision_clearance_residual_objective: 7
  speed_floor_context_guard_objective: 1

identity guards:
  success_identity_guard: 13

blocked stale guardrails:
  actor_head_delta_execution_admission_blocked_stale_fixed_surface: 11
```

## M2973 Trace-Panel Design

M2973 should produce a trace panel that is useful for later residual fitting
without pretending that fitting has already happened.

Allowed M2973 work:

```text
load parent checkpoint read-only
instantiate the actor-head delta wrapper with zero residual identity
resolve M2970 candidate and guard rows
collect or export deployable observation/action/response traces for admitted rows
record parent action, residual limit, bounded action range, and actor contract metadata
record row-level trace availability and failure reasons
write a result-audit follow-up manifest
```

M2973 may run bounded diagnostic reset/step/rollout only for trace collection
and only under the existing actor 72/action 3 contract. It must keep those rows
out of validation, paper, high-fidelity, self-ID, and promotion denominators.

Forbidden M2973 work:

```text
no residual fitting
no PPO update
no supervised actor update
no validation run
no ranking or winner selection
no checkpoint save mutation or promotion
no performance or repair-success verdict
no paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim
```

## Actor Boundary

M2973 must keep the actor input deployable:

```text
actor observation/action remains 72/action 3
hidden/oracle/future-target actor input remains false
route/source/evaluator/diagnostic/success/progress/objective/admission/verdict labels actor-visible remains false
mu, mass, tire stiffness, brake scale, actuator tau, slip, tire force, TTC, oracle feasibility, reference trajectory, speed_ref, beta_target, path error, heading error, path curvature, required clearance, and oracle stopping distance remain actor-invisible
```

Trace-panel metadata may include objective family, outcome family, row status,
source milestone, and gate decisions, but those fields remain evaluator/trainer
metadata only. They cannot enter actor observations.

## M2973 Output Contract

M2973 should write:

```text
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/summary.json
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/trace_source_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/trace_panel_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/trace_guard_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/trace_availability_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/actor_contract_guard_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/claim_boundary_rows.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/gate_matrix.csv
runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/run_state.json
docs/m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight.md
experiments/manifests/m2974-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-result-audit.json
```

`trace_panel_rows.csv` must include at least:

```text
trace_panel_row_id
training_admission_candidate_id
execution_candidate_id
workload_id
task_family
outcome_family
objective_family
trace_role
trace_available
trace_step_count
actor_observation_dim
actor_action_dim
parent_checkpoint_loaded_read_only
zero_residual_identity_mode
residual_delta_abs_max
actor_visible_label
hidden_oracle_actor_input_required
future_target_actor_input_required
training_started
ppo_run
ranking_run
checkpoint_mutated
validation_denominator_allowed
paper_denominator_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
claim_boundary
```

## Gate Matrix

M2973 passes only if all of these hold:

```text
M2971 audit exists and accepts M2970
M2970 status_pass true
M2970 gate_matrix_pass true
43 future training candidate rows accounted
13 success identity guard rows accounted
11 stale guardrails accounted and non-executed
trace availability is explicit for every admitted candidate and guard row
actor observation/action remains 72/action 3
hidden/oracle/future-target actor input remains false
objective/admission/verdict labels actor-visible remains false
training_started false
ppo_run false
ranking_run false
winner_selected false
checkpoint_mutated false
checkpoint_promoted false
repair_success_claim_made false
driver_performance_claim_made false
validation_readiness_claim_made false
paper_claim_made false
current_sim_verdict_claim_made false
high_fidelity_validation_claim_made false
finite_window_vs_gru_claim_made false
full_ideal_driver_completion_claim_made false
level3_self_id_claim_made false
all required artifacts present
one result-audit follow-up manifest registered
```

## Follow-Up

M2972 admits:

```text
m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight
```

M2973 should be a bounded data-panel preflight. It can be counted as a new
dataset/panel surface only if it writes explicit trace availability and actor
contract rows. It must register M2974 result audit before any residual fitting,
training, validation, ranking, promotion, performance, paper, current-sim,
high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.
