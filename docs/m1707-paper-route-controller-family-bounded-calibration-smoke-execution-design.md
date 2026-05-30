# M1707 Paper-Route Controller-Family Bounded Calibration Smoke Execution Design

- status: completed
- decision: `bounded_calibration_smoke_execution_design_admit_measured_execution`
- parent audit: `docs/m1706-paper-route-controller-family-bounded-calibration-smoke-preflight-result-audit.md`
- bounded matrix: `runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_smoke_matrix.csv`

## Summary

M1707 designs measured execution for the M1705 bounded calibration smoke.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Scope

M1708 should execute exactly the M1705 bounded matrix:

```text
selected base specs: 6
bounded calibration specs: 72
profiles: 12
episodes: 864
```

Execution must be resumable and must preserve every row from
`bounded_smoke_matrix.csv`. The task source is calibration-specific, so M1708
should use a bounded-calibration runner or adapter instead of the default M1693
full-rollout inputs.

Required inputs:

```text
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_calibration_specs.json
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_smoke_matrix.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
```

## Required Output Directory

M1708 should write:

```text
runs/m1708_controller_family_bounded_calibration_smoke_execution/summary.json
runs/m1708_controller_family_bounded_calibration_smoke_execution/episode_rows.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/failure_rows.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/run_state.json
runs/m1708_controller_family_bounded_calibration_smoke_execution/profile_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/calibration_variant_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/task_family_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/source_edge_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/outcome_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/termination_reason_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/profile_outcome_aggregate.csv
```

## Required Episode Fields

Each `episode_rows.csv` row must retain:

```text
calibration_workload_id
calibration_spec_id
base_task_source_id
profile_name
task_family
source_edge
window_tag
executable_source_family
env_template_family
track_width_scale
finish_variant
max_steps_scale
outcome_bucket
termination_reason
success
collision
obstacle_completed
min_clearance_margin
return
steps
eval_seed
```

Guardrail fields must remain false:

```text
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
```

## Required Aggregates

M1708 should aggregate first by task-quality keys, not by profile rank:

```text
track_width_scale + finish_variant + max_steps_scale
task_family
source_edge
profile_name
outcome_bucket
termination_reason
profile_name + outcome_bucket
```

Required metrics per aggregate:

```text
episode_count
success_obstacle_pass_rate
collision_failure_rate
off_track_noncollision_noncompletion_rate
max_steps_noncompletion_rate
safe_noncollision_noncompletion_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
all_selected_metrics_finite
```

## Diagnostic Decision Rules For M1709

M1708 execution itself should not interpret results beyond pass/fail plumbing.
M1709 should audit task quality with these pre-registered rules:

```text
execution pass:
  episode_count == 864
  failure_count == 0
  all_selected_metrics_finite == true
  guardrail_violation_count == 0

interpretable calibration variant:
  variant episode_count == 72
  off_track_noncollision_noncompletion_rate <= 0.70

weak but useful calibration signal:
  best variant off_track_noncollision_noncompletion_rate <= 0.80
  or best variant improves off-track rate by at least 0.10
     against the original track_width=1.0 finish=original max_steps=1.0 baseline

task-quality repair:
  all variants remain off-track dominated above 0.80
  or collision/outcome aggregates are missing
  or profile/control rows are invalid
```

These rules are about task quality. They do not promote a driver or rank
controller families.

## Claim Boundary

Allowed after M1708:

```text
bounded public execution completed;
task-quality calibration outcomes are available for audit;
off-track/collision/pass outcome modes can be inspected.
```

Forbidden after M1708:

```text
controller-family ranking;
finite-window history necessity;
recurrent advantage;
private-holdout generalization;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1708 measured bounded calibration smoke execution. M1708 may implement a
bounded-calibration runner or adapter if needed, but must not train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking.
