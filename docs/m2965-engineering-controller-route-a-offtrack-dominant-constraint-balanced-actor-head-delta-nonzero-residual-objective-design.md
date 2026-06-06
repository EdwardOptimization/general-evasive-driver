# M2965 Engineering Controller Route A Actor-Head Delta Nonzero Residual Objective Design

## Metadata

- status: completed
- decision: `admit_m2966_nonzero_residual_objective_materialization_preflight`
- manifest: `experiments/manifests/m2965-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-design.json`
- parent audit: `docs/m2964-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-zero-residual-failure-localization-objective-admission-result-audit.md`
- parent summary: `runs/m2963_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_post_zero_residual_failure_localization_objective_admission_preflight/summary.json`
- parent objective rows: `runs/m2963_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_post_zero_residual_failure_localization_objective_admission_preflight/residual_objective_admission_rows.csv`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight.json`
- next: `m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight`

## Design Decision

M2965 admits exactly one next route:

```text
m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight
```

M2965 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, rank, promote, mutate checkpoints, execute dependency work,
select a winner, compute a success-rate verdict, or claim implementation
readiness, repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity readiness, full-driver completion, finite-window-vs-GRU
evidence, or self-ID evidence.

The immediate route is not behavior execution. It is a no-execution objective
materialization preflight that must turn the audited M2963 residual-objective
admission rows into machine-checkable objective, guard, actor-contract, and
claim-boundary rows before any residual fitting can be considered.

## Design Premise

M2964 accepts M2963 as complete and claim-safe:

```text
status_pass: true
gate_matrix_pass: true
failure-localization rows: 56
residual-objective admission rows: 4
residual objectives admitted for later design: 3
blocked stale fixed-source guardrails: 11
actor observation/action: 72/action 3
training_run: false
execution_run: false
ranking_run: false
checkpoint_promoted: false
```

The accepted objective-admission rows are:

```text
collision_clearance_residual_objective: 7 rows, admitted for audit/design
offtrack_recovery_residual_objective: 35 rows, admitted for audit/design
speed_floor_context_guard_objective: 1 row, admitted for audit/design
success_identity_guard: 13 rows, guard context only
```

The design must remain constraint-balanced. A nonzero residual objective that
only reduces off-track count while increasing collisions, crawl behavior, or
success-row action drift is not admitted by M2965.

## Objective Surface

M2966 should materialize one objective design with these components:

```text
primary objective:
  offtrack_recovery_residual_objective
  source rows: 35 off_track zero-residual diagnostics
  intended role: admit later residual fitting pressure against off-track failure contexts

secondary safety objective:
  collision_clearance_residual_objective
  source rows: 7 collision zero-residual diagnostics
  intended role: block off-track improvement through collision substitution

context guard:
  speed_floor_context_guard_objective
  source rows: 1 speed_too_low zero-residual diagnostic
  intended role: block crawl or stall substitution

identity guard:
  success_identity_guard
  source rows: 13 diagnostic_success rows
  intended role: keep residual near zero on already-successful zero-residual contexts
```

The identity guard is not a positive training target. It is a regression guard
against unnecessary residual action movement.

## Actor And Training Boundary

M2966 must keep all objective labels outside the actor input. Objective family,
outcome family, admission status, success identity, row lineage, aggregate
counts, and gate decisions may be trainer/evaluator-side metadata in a later
manifest, but they are not actor-visible observations.

Required actor and residual boundaries:

```text
actor observation/action remains 72/action 3
parent actor checkpoint is read-only
residual head initialization is zero identity
residual delta remains bounded before action combination
combined action remains clipped to deployed action range
hidden/oracle/future-target actor input remains false
route/source/evaluator/diagnostic/success/progress/objective/admission/verdict labels actor-visible remains false
success identity guard rows cannot become positive residual targets
11 blocked stale fixed-source rows remain non-executed guardrails
```

M2966 must not schedule training or execution. It may only write objective
materialization artifacts and a follow-up result-audit manifest.

## M2966 Output Contract

M2966 should write:

```text
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/summary.json
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/objective_family_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/objective_component_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/row_assignment_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/success_identity_guard_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/stale_guardrail_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/actor_contract_guard_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/claim_boundary_rows.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/gate_matrix.csv
runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/run_state.json
docs/m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight.md
experiments/manifests/m2967-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-result-audit.json
```

`objective_family_rows.csv` must include at least:

```text
objective_family
source_trigger_outcome
source_row_count
admitted_for_materialization
future_training_manifest_required
future_execution_manifest_required
training_scheduled
execution_scheduled
ranking_allowed
winner_selection_allowed
promotion_allowed
ordinary_engineering_denominator_allowed
validation_denominator_allowed
paper_denominator_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
actor_input_change_required
actor_visible_labels_required
claim_boundary
```

`row_assignment_rows.csv` must account for all 56 M2963 localized rows and must
not drop failed rows or success guard rows. It must carry the source milestone,
task family, outcome family, workload identity, row identity, objective family,
guard status, and claim-boundary flags.

## Gate Matrix

M2966 passes only if all of these hold:

```text
M2964 audit exists and accepts M2963
M2963 status_pass true
M2963 gate_matrix_pass true
56 M2963 failure-localization rows loaded and accounted
4 M2963 residual-objective admission rows loaded and accounted
3 non-success objective families materialized as design inputs only
13 diagnostic_success rows materialized only as success identity guard rows
11 blocked stale fixed-source rows preserved as non-executed guardrails
actor observation/action remains 72/action 3
hidden/oracle/future-target actor input remains false
objective/admission/verdict labels actor-visible remains false
environment_reset_scheduled false
rollout_scheduled false
training_scheduled false
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

M2965 admits:

```text
m2966-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-objective-materialization-preflight
```

M2966 must be no-execution materialization only. It must register M2967 result
audit before any interpretation, residual training, repair execution,
validation, ranking, promotion, performance, paper, current-sim, high-fidelity,
full-driver, finite-window-vs-GRU, or self-ID claim.
