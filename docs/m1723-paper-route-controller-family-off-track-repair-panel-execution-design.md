# M1723 Paper-Route Controller-Family Off-Track Repair Panel Execution Design

- status: completed
- decision: `off_track_repair_panel_execution_design_admit_measured_execution`
- parent audit: `docs/m1722-paper-route-controller-family-off-track-repair-panel-preflight-result-audit.md`
- repair panel matrix: `runs/m1721_off_track_repair_panel_preflight/repair_panel_matrix.csv`

## Summary

M1723 designs measured execution for the M1721 off-track repair panel.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, rank
controller families, or claim paper-level evidence or level3 self-identification.

## Execution Scope

M1724 should execute exactly the M1721 repair panel matrix:

```text
selected base specs: 18
repair panel specs: 72
profiles: 12
episodes: 864
task split: T4=12, T5=6
variant labels: original_axis_baseline, best_off_track_variant,
                collision_control_wide_relaxed, wide_relaxed_extended
```

Execution must be resumable and must preserve every row from
`repair_panel_matrix.csv`. The runner may reuse the M1715 calibrated-scale-up
execution logic, but it must consume the repair-panel key names and retain
`repair_variant_label` and `repair_panel_workload_id` in every output row.

Required inputs:

```text
runs/m1721_off_track_repair_panel_preflight/repair_panel_specs.json
runs/m1721_off_track_repair_panel_preflight/repair_panel_matrix.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
```

## Required Output Directory

M1724 should write:

```text
runs/m1724_off_track_repair_panel_execution/summary.json
runs/m1724_off_track_repair_panel_execution/episode_rows.csv
runs/m1724_off_track_repair_panel_execution/failure_rows.csv
runs/m1724_off_track_repair_panel_execution/run_state.json
runs/m1724_off_track_repair_panel_execution/profile_aggregate.csv
runs/m1724_off_track_repair_panel_execution/repair_variant_aggregate.csv
runs/m1724_off_track_repair_panel_execution/task_family_aggregate.csv
runs/m1724_off_track_repair_panel_execution/source_edge_aggregate.csv
runs/m1724_off_track_repair_panel_execution/outcome_aggregate.csv
runs/m1724_off_track_repair_panel_execution/termination_reason_aggregate.csv
runs/m1724_off_track_repair_panel_execution/profile_outcome_aggregate.csv
```

## Required Episode Fields

Each `episode_rows.csv` row must retain:

```text
repair_panel_workload_id
calibration_workload_id
calibration_spec_id
repair_variant_label
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

M1724 should aggregate by task-quality repair keys, not by profile rank:

```text
repair_variant_label
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

## Diagnostic Decision Rules For M1725

M1724 execution itself should not interpret results beyond pass/fail plumbing.
M1725 should audit task quality with these pre-registered rules:

```text
execution pass:
  episode_count == 864
  failure_count == 0
  all_selected_metrics_finite == true
  guardrail_violation_count == 0
  repair_variant_aggregate.csv exists and includes all four labels
  outcome and termination aggregates exist

baseline:
  original_axis_baseline is the baseline variant

variant comparison:
  offtrack_improvement = baseline_offtrack_rate - variant_offtrack_rate
  collision_delta = variant_collision_rate - baseline_collision_rate
  prior_control_best_offtrack =
    min(best_off_track_variant_offtrack,
        collision_control_wide_relaxed_offtrack)
  composite_delta_vs_prior_best =
    wide_relaxed_extended_offtrack - prior_control_best_offtrack

full repair positive:
  wide_relaxed_extended has
    off_track_noncollision_noncompletion_rate <= 0.70
    and collision_delta <= 0.05

composite repair positive:
  wide_relaxed_extended has
    composite_delta_vs_prior_best <= -0.03
    and offtrack_improvement >= 0.10
    and collision_delta <= 0.05

conditional repair positive:
  if the composite does not win,
  at least one calibrated variant has
    offtrack_improvement >= 0.10
    and collision_delta <= 0.05

tradeoff-only:
  off-track improves but collision_delta > 0.05

repair failure:
  all calibrated variants remain off-track dominated above 0.80
  or no calibrated variant improves off-track rate by at least 0.10
  or required aggregates are missing
```

The audit must compare all three non-baseline variants separately:

```text
best_off_track_variant
collision_control_wide_relaxed
wide_relaxed_extended
```

It must not choose a single best row after seeing results and turn that into a
profile or controller-family ranking.

## Claim Boundary

Allowed after M1724:

```text
repair-panel public diagnostic execution completed;
repair variant outcome and termination aggregates are available for audit;
collision/off-track repair tradeoffs can be inspected under M1725 rules.
```

Forbidden after M1724:

```text
controller-family ranking;
finite-window history necessity;
recurrent advantage;
private-holdout generalization;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1724 measured off-track repair panel execution. M1724 may implement a
repair-panel execution runner or adapter if needed, but must not train, replay,
run PPO, promote, use private holdout, change actor inputs, tune profiles, or
claim controller-family ranking.
