# M1714 Paper-Route Controller-Family Calibrated Scale-Up Execution Design

- status: completed
- decision: `calibrated_scale_up_execution_design_admit_measured_execution`
- parent audit: `docs/m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit.md`
- scale-up matrix: `runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv`

## Summary

M1714 designs measured execution for the M1712 source-expanded calibrated
scale-up subset.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Scope

M1715 should execute exactly the M1712 scale-up matrix:

```text
selected base specs: 18
scale-up calibration specs: 72
profiles: 12
episodes: 864
task split: T4=9, T5=9
variant labels: original_axis_baseline, best_off_track_variant,
                collision_control_wide_relaxed, mid_calibration_variant
```

Execution must be resumable and must preserve every row from
`scale_up_matrix.csv`. The runner may reuse the M1708 bounded-calibration
execution logic, but it must consume the scale-up key names and retain
`scale_up_variant_label` and `scale_up_workload_id` in every output row.

Required inputs:

```text
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.json
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
```

## Required Output Directory

M1715 should write:

```text
runs/m1715_controller_family_calibrated_scale_up_execution/summary.json
runs/m1715_controller_family_calibrated_scale_up_execution/episode_rows.csv
runs/m1715_controller_family_calibrated_scale_up_execution/failure_rows.csv
runs/m1715_controller_family_calibrated_scale_up_execution/run_state.json
runs/m1715_controller_family_calibrated_scale_up_execution/profile_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/scale_up_variant_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/task_family_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/source_edge_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/outcome_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/termination_reason_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/profile_outcome_aggregate.csv
```

## Required Episode Fields

Each `episode_rows.csv` row must retain:

```text
scale_up_workload_id
calibration_workload_id
calibration_spec_id
scale_up_variant_label
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

M1715 should aggregate by task-quality and coverage keys, not by profile rank:

```text
scale_up_variant_label
profile_name
task_family
source_edge
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

## Diagnostic Decision Rules For M1716

M1715 execution itself should not interpret results beyond pass/fail plumbing.
M1716 should audit task quality with these pre-registered rules:

```text
execution pass:
  episode_count == 864
  failure_count == 0
  all_selected_metrics_finite == true
  guardrail_violation_count == 0
  scale_up_variant_aggregate.csv exists and includes all four labels
  outcome and termination aggregates exist

baseline:
  original_axis_baseline is the baseline variant

variant comparison:
  offtrack_improvement = baseline_offtrack_rate - variant_offtrack_rate
  collision_delta = variant_collision_rate - baseline_collision_rate

positive scale-up:
  at least one calibrated variant has
    off_track_noncollision_noncompletion_rate <= 0.70
    and collision_delta <= 0.05

conditional positive:
  if no calibrated variant crosses the 0.70 off-track threshold,
  at least one calibrated variant has
    offtrack_improvement >= 0.10
    and collision_delta <= 0.05

tradeoff-only:
  off-track improves but collision_delta > 0.05

repair:
  all calibrated variants remain off-track dominated above 0.80
  or no calibrated variant improves off-track rate by at least 0.10
  or required aggregates are missing
```

The audit must compare the three calibrated variants separately:

```text
best_off_track_variant
collision_control_wide_relaxed
mid_calibration_variant
```

It must not choose a single best row after seeing results and then turn that
into a profile or controller-family ranking.

## Claim Boundary

Allowed after M1715:

```text
source-expanded public diagnostic execution completed;
scale-up variant outcome and termination aggregates are available for audit;
collision/off-track tradeoffs can be inspected under the M1716 rules.
```

Forbidden after M1715:

```text
controller-family ranking;
finite-window history necessity;
recurrent advantage;
private-holdout generalization;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1715 measured calibrated scale-up execution. M1715 may implement a
scale-up execution runner or adapter if needed, but must not train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking.
