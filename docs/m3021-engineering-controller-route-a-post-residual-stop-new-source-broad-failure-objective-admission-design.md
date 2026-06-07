# M3021 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Objective Admission Design

## Metadata

- status: completed
- decision: `admit_m3022_new_source_broad_failure_objective_contract_materialization_preflight`
- manifest: `experiments/manifests/m3021-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-admission-design.json`
- parent synthesis: `docs/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.md`
- parent audit: `docs/m3019-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-result-audit.md`
- parent preflight: `runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m3022-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-preflight.json`
- next: `m3022-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-preflight`

## Design Decision

M3021 admits exactly one next route:

```text
m3022-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-preflight
```

M3021 is design-only. It does not reset, step, roll out, replay, validate,
train, run PPO, fit targets, rank profiles, select a winner, promote, mutate
checkpoints, tune profiles, compute a success-rate verdict, or claim repair
success, driver performance, paper evidence, current-sim verdict,
high-fidelity readiness, full-driver completion, finite-window-vs-GRU
evidence, or self-ID evidence.

The admitted next route is also no-execution. M3022 may only materialize a
machine-checkable objective contract from the M3018/M3019/M3020 diagnostic
evidence. That contract must preserve the full 32-row denominator, the 16
task_source ids, both read-only profile bindings, and all guard contexts before
any later target materialization, fitting, execution, ranking, validation, or
promotion can be considered.

## Design Premise

M3020 accepts M3018/M3019 only as claim-safe failure-localization evidence:

```text
M3018 status_pass: true
M3018 gate_matrix_pass: true
M3018 required_artifacts_present: true
source specs: 16
unique task_source ids: 16
failure-localization rows: 32
profile/source aggregate rows: 32
profile bindings: 2
actor observation/action: 72/action 3
candidate success count: 0/16
parent success count: 3/16
task_source ids non-success under both profiles: 13/16
```

The diagnostic surface is broad and negative:

```text
success rows: 3
collision rows: 5
off_track terminations: 23
obstacle_collision terminations: 4
speed_too_low terminations: 2
blank termination rows: 3
```

The failure-family distribution must be preserved:

```text
offtrack_recovery_failure: 17
offtrack_high_severity_recovery_failure: 5
collision_clearance_failure: 5
speed_floor_context: 2
success_context: 3
```

This is not a repair target. It is an objective-admission surface that says
future work must be constraint-balanced: offtrack pressure alone is illegal if
it can trade off into collision, speed-floor collapse, or action drift on
already-successful contexts.

## Admitted Objective Contract

M3022 should materialize one broad-failure objective contract with these
families:

```text
primary recovery family:
  offtrack_recovery_broad_failure_contract
  source rows: 22 offtrack recovery contexts
  intended role: preserve offtrack-dominant failure pressure as later design input only

secondary safety family:
  collision_clearance_guard_contract
  source rows: 5 collision or obstacle-collision contexts
  intended role: block offtrack repair routes that substitute collisions

speed floor guard:
  speed_floor_guard_contract
  source rows: 2 speed_too_low contexts
  intended role: block crawl, stall, or speed-collapse substitutions

success identity guard:
  success_identity_context_guard
  source rows: 3 success_context rows
  intended role: preserve already-successful parent contexts as no-regression guard context
```

The success identity guard is not a positive training target. It is a future
regression guard against unnecessary action movement.

M3022 must not choose a numeric target, loss weight, residual value, checkpoint,
profile winner, validation denominator, or promotion candidate. It may only
turn the admitted contract into auditable rows.

## Actor And Claim Boundary

M3022 must keep every objective label outside the actor input. Objective
family, failure family, profile binding, task_source id, diagnostic outcome,
success context, admission state, and gate decisions may only be
trainer/evaluator-side metadata for a later manifest.

Required boundaries:

```text
actor observation/action remains 72/action 3
parent and candidate checkpoints remain read-only
no hidden dynamics actor input
no oracle labels actor input
no future target actor input
no source, route, outcome, objective, success, progress, verdict, or TTC actor input
no environment reset, step, rollout, replay, validation, training, PPO, ranking, promotion, checkpoint mutation, or profile tuning in M3022
no target materialization, residual fitting, repair-success claim, performance claim, paper claim, current-sim verdict, high-fidelity claim, finite-window-vs-GRU claim, full-driver claim, or self-ID claim in M3022
```

## M3022 Output Contract

M3022 should write:

```text
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/summary.json
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/objective_family_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/objective_component_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/row_assignment_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/profile_source_guard_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/actor_contract_guard_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/claim_boundary_rows.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/gate_matrix.csv
runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/run_state.json
docs/m3022-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-preflight.md
experiments/manifests/m3023-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-result-audit.json
```

`row_assignment_rows.csv` must account for all 32 M3018 localization rows and
must not drop candidate rows, parent rows, collision rows, speed-floor rows, or
success-context guard rows.

`objective_family_rows.csv` must include at least:

```text
objective_family
source_failure_family
source_row_count
admitted_for_contract_materialization
future_target_materialization_manifest_required
future_fitting_manifest_required
future_execution_manifest_required
training_scheduled
execution_scheduled
ranking_allowed
winner_selection_allowed
promotion_allowed
validation_denominator_allowed
performance_claim_allowed
paper_claim_allowed
high_fidelity_readiness_allowed
self_id_claim_allowed
actor_input_change_required
actor_visible_labels_required
claim_boundary
```

## Gate Matrix

M3022 passes only if all of these hold:

```text
M3020 synthesis exists and admits M3021
M3019 audit exists and accepts M3018
M3018 status_pass true
M3018 gate_matrix_pass true
M3018 required_artifacts_present true
32 M3018 failure-localization rows loaded and accounted
32 M3018 profile/source aggregate rows loaded and accounted
16 task_source ids preserved
2 read-only profile bindings preserved
offtrack collision speed-floor and success-context families preserved
3 success_context rows remain guard context only
actor observation/action remains 72/action 3
hidden/oracle/future-target/source/route/outcome/progress/verdict/TTC actor input remains false
environment_reset_scheduled false
rollout_scheduled false
target_materialization_scheduled false
training_scheduled false
ppo_scheduled false
ranking_run false
winner_selected false
checkpoint_mutated false
checkpoint_promoted false
validation_result_claim_made false
repair_success_claim_made false
driver_performance_claim_made false
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

M3021 admits:

```text
m3022-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-preflight
```

M3022 must be no-execution materialization only. It must register M3023 result
audit before any interpretation, target materialization, fitting, execution,
validation, ranking, promotion, repair-success claim, performance claim, paper
claim, current-sim verdict, high-fidelity claim, full-driver claim,
finite-window-vs-GRU claim, or self-ID claim.
