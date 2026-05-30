# M1730 Paper-Route Task-Quality Scenario Taxonomy Execution Design

- status: completed
- decision: `scenario_taxonomy_execution_design_admit_measured_execution`
- parent audit: `docs/m1729-paper-route-task-quality-scenario-taxonomy-preflight-result-audit.md`
- scenario matrix: `runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_matrix.csv`
- scenario specs: `runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.json`

## Summary

M1730 designs measured execution for the M1728 scenario taxonomy matrix.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, rank
controller families, treat unsupported faults as covered, or claim paper-level
evidence or level3 self-identification.

## Execution Scope

M1731 should execute exactly the M1728 scenario taxonomy matrix:

```text
scenario families: 6
scenario specs: 72
profiles: 12
episodes: 864
```

Required inputs:

```text
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_matrix.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/unsupported_scenario_features.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
```

The runner must use `scenario_specs.json` as the source of executable
`env_config` and scenario metadata. `scenario_matrix.csv` only schedules profile
cells.

## Required Metadata Join

Every episode row must copy these fields from `scenario_specs.json`:

```text
scenario_family_id
scenario_family
scenario_role
obstacle_timing_bucket
obstacle_lateral_bucket
road_boundary_bucket
hidden_dynamics_bucket
template_source_family
allowed_labels_metadata_only
labels_enter_actor_input
```

`allowed_labels_metadata_only` and `scenario_family` are never actor inputs.
They are metadata for audit and aggregation.

## Required Output Directory

M1731 should write:

```text
runs/m1731_task_quality_scenario_taxonomy_execution/summary.json
runs/m1731_task_quality_scenario_taxonomy_execution/episode_rows.csv
runs/m1731_task_quality_scenario_taxonomy_execution/failure_rows.csv
runs/m1731_task_quality_scenario_taxonomy_execution/run_state.json
runs/m1731_task_quality_scenario_taxonomy_execution/profile_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_family_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_role_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/road_boundary_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/obstacle_timing_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/termination_reason_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/profile_outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_family_outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/unsupported_scenario_features.csv
```

## Required Episode Fields

Each `episode_rows.csv` row must retain:

```text
scenario_workload_id
scenario_spec_id
scenario_family_id
scenario_family
scenario_role
profile_name
obstacle_timing_bucket
obstacle_lateral_bucket
road_boundary_bucket
hidden_dynamics_bucket
template_source_family
allowed_labels_metadata_only
labels_enter_actor_input
success
collision
obstacle_completed
min_clearance_margin
termination_reason
outcome_bucket
return
steps
eval_seed
profile_config_path
checkpoint_path
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
unsupported_faults_treated_as_covered
```

## Required Aggregates

M1731 should aggregate by scenario structure, not by profile rank:

```text
profile_name
scenario_family
scenario_role
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
outcome_bucket
termination_reason
profile_name + outcome_bucket
scenario_family + outcome_bucket
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

## Execution Pass/Fail Rules

M1731 passes as execution plumbing only if:

```text
episode_count == 864
failure_count == 0
all_selected_metrics_finite == true
guardrail_violation_count == 0
scenario_family_aggregate_rows == 6
hidden_dynamics_bucket_aggregate_rows > 0
outcome_aggregate_rows > 0
termination_reason_aggregate_rows > 0
scenario_family_outcome_aggregate_rows > 0
unsupported_scenario_feature_count == 5
silent_unsupported_approximation_count == 0
unsupported_faults_treated_as_covered == false
```

M1731 must not interpret controller-family ranking. Result interpretation is
deferred to M1732.

## Unsupported Feature Boundary

M1731 must copy `unsupported_scenario_features.csv` to its output directory and
include these summary fields:

```text
unsupported_scenario_feature_count
silent_unsupported_approximation_count
unsupported_faults_treated_as_covered
```

The value of `unsupported_faults_treated_as_covered` must be `false`. Current
M1728 execution covers supported hidden dynamics stressors, not single-wheel
faults, half-shaft faults, or side-specific brake imbalance.

## Claim Boundary

Allowed after M1731:

```text
scenario-taxonomy public diagnostic execution completed;
scenario family and hidden dynamics aggregates are available for audit;
unsupported fault boundaries are preserved.
```

Forbidden after M1731:

```text
controller-family ranking;
scenario taxonomy quality conclusion before M1732 audit;
private-holdout generalization;
finite-window history necessity;
recurrent advantage;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1731 measured scenario taxonomy execution. M1731 may implement a
scenario-taxonomy execution runner, but must not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, treat
unsupported faults as covered, or rank controller families.
