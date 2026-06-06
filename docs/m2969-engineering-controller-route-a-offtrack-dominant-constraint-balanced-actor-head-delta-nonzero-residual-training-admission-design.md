# M2969 Engineering Controller Route A Actor-Head Delta Nonzero Residual Training Admission Design

## Metadata

- status: completed
- decision: `admit_m2970_nonzero_residual_training_admission_materialization_preflight`
- manifest: `experiments/manifests/m2969-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-design.json`
- parent synthesis: `docs/m2968-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-branch-synthesis.md`
- parent audit: `docs/m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-result-audit.md`
- parent summary: `runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight.json`
- next: `m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight`

## Design Decision

M2969 admits exactly one next route:

```text
m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight
```

M2969 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, rank, promote, mutate checkpoints, execute dependency work,
select a winner, compute a success-rate verdict, or claim implementation
readiness, repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity readiness, full-driver completion, finite-window-vs-GRU
evidence, or self-ID evidence.

The next route is not training. It is a no-execution materialization preflight
that must convert the accepted M2966 objective surface into auditable training
admission rows before any residual fitting can be considered.

## Admission Surface

M2969 consumes the accepted M2966/M2967/M2968 chain:

```text
M2966 status_pass: true
M2966 gate_matrix_pass: true
objective family rows: 4
objective component rows: 4
row assignment rows: 56
success identity guard rows: 13
stale guardrail rows: 11
actor guard rows: 12
claim boundary rows: 23
gate rows: 17
```

M2969 admits a training-admission materialization over these roles:

```text
training candidate rows after future audit: 43
  offtrack_recovery_residual_objective: 35
  collision_clearance_residual_objective: 7
  speed_floor_context_guard_objective: 1

identity guard rows: 13
  success_identity_guard: 13

non-executed stale guardrails: 11
```

The 43 non-success rows are admitted only to M2970 materialization. They are not
training instructions yet. The 13 success rows are identity guards only. The 11
stale fixed-source rows remain outside training, execution, validation, paper,
high-fidelity, and self-ID denominators.

## Guarded Training Admission Design

M2970 should materialize one guarded residual training-admission design with
these trainer-side components:

```text
primary objective:
  offtrack_recovery_residual_objective
  candidate rows: 35
  role: recovery pressure only after future audit

collision guard:
  collision_clearance_residual_objective
  candidate rows: 7
  role: prevent off-track gains through collision substitution

speed guard:
  speed_floor_context_guard_objective
  candidate rows: 1
  role: prevent crawl/stall substitution

identity guard:
  success_identity_guard
  guard rows: 13
  role: keep residual near zero on already-successful zero-residual contexts

stale guardrail:
  actor_head_delta_execution_admission_blocked_stale_fixed_surface
  guard rows: 11
  role: excluded from training and denominators
```

The future training preflight, if later admitted by audit, must be bounded by:

```text
parent checkpoint loaded read-only before admission audit
residual head initialized to zero identity
residual delta bounded before action combination
combined action clipped to deployed [steer, throttle, brake] range
no checkpoint save mutation ranking or promotion before a separate audit
no validation denominator or performance verdict
```

## Actor Boundary

M2970 and any later training preflight must keep all objective/admission labels
outside the actor input. Objective family, row assignment, success identity,
guardrail status, source milestone, task family, training-admission status, and
gate decisions may be trainer/evaluator metadata only.

Required actor contract:

```text
actor observation/action remains 72/action 3
hidden/oracle/future-target actor input remains false
route/source/evaluator/diagnostic/success/progress/objective/admission/verdict labels actor-visible remains false
mu, mass, tire stiffness, brake scale, actuator tau, slip, tire force, TTC, oracle feasibility, reference trajectory, speed_ref, beta_target, path error, heading error, path curvature, required clearance, and oracle stopping distance remain actor-invisible
```

## M2970 Output Contract

M2970 should write:

```text
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/summary.json
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/training_admission_profile_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/training_admission_candidate_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/training_admission_guard_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/objective_balance_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/success_identity_guard_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/stale_guardrail_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/claim_boundary_rows.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/gate_matrix.csv
runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/run_state.json
docs/m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight.md
experiments/manifests/m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-result-audit.json
```

`training_admission_candidate_rows.csv` must account for all 43 non-success
training candidates and must include at least:

```text
training_admission_candidate_id
source_row_assignment_id
localization_row_id
execution_candidate_id
source_milestone
task_family
workload_id
outcome_family
objective_family
training_admission_status
future_training_manifest_required
future_execution_manifest_required
training_scheduled
execution_scheduled
ranking_allowed
winner_selection_allowed
promotion_allowed
actor_visible_label
validation_denominator_allowed
paper_denominator_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
claim_boundary
```

M2970 must also carry all 13 success identity guards and 11 stale guardrails in
dedicated guard artifacts. A pass must not drop any of these rows.

## Gate Matrix

M2970 passes only if all of these hold:

```text
M2968 synthesis exists and continues to M2969/M2970
M2967 audit accepts M2966
M2966 status_pass true
M2966 gate_matrix_pass true
56 row assignments loaded and accounted
43 non-success training candidates materialized
13 success identity guards materialized and not positive training targets
11 stale guardrails materialized and non-executed
4 objective families and 4 objective components accounted
actor observation/action remains 72/action 3
hidden/oracle/future-target actor input remains false
objective/admission/verdict labels actor-visible remains false
training_scheduled false
execution_scheduled false
ppo_scheduled false
ranking_run false
winner_selected false
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

M2969 admits:

```text
m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight
```

M2970 must be no-execution materialization only. It must register M2971 result
audit before any training, PPO, replay, residual fitting, execution,
validation, ranking, promotion, performance, paper, current-sim, high-fidelity,
full-driver, finite-window-vs-GRU, or self-ID claim.
