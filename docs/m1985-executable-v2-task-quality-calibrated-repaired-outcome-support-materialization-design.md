# M1985 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Materialization Design

- status: completed
- decision: `task_quality_calibrated_outcome_support_materialization_design_admit_implementation`
- parent audit: `docs/m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit.md`
- source rows: `runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv`
- accepted cells: `runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv`
- materialization execution in M1985: `false`
- reset/rollout/measured execution in M1985: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1983/M1984 prove that the outcome-support repair templates have enough
no-rollout source support for materialization design. M1985 fixes the bounded
subset and representative-cell rules before any executable specs are written.

This remains task-quality infrastructure. It is not reset validation, measured
execution, controller ranking, paper-level evidence, or self-ID evidence.

## Selection Inputs

M1986 should read:

```text
--source-rows
  runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv

--accepted-cells
  runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv

--profile-run-dir
  runs/m1674_controller_family_one_seed_public_pilot

--output-dir
  runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight

--next-blocker
  m1987-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-result-audit
```

No source mining rerun is allowed in M1986. It must materialize only from the
already audited M1983 artifacts.

## Source Eligibility

Eligible source rows must satisfy:

```text
source_support_status == supported
labels_enter_actor_input == false
v2_ranking_admissible_by_default == false
profile_specific_tuning == false
```

Rows in `outcome_support_blocked_rows.csv` are excluded from the first
materialization subset. They remain diagnostic rows for a possible later source
repair but must not be materialized now.

Private holdout is not used in this repair branch.

## Target Subset

M1986 should materialize:

```text
selected_source_count: 80
controller_profiles_per_source: 12
planned_workload_rows: 960
```

Repair-axis quotas:

```text
offtrack_anchor_relief: 24
offtrack_boundary_relief_extension: 16
success_support_expansion: 20
collision_mitigation_relief: 12
mitigation_metric_isolation: 8
```

Rationale:

- offtrack-anchor and offtrack-boundary rows repair the dominant offtrack-only
  blocker and now have full source support;
- success-support rows preserve positive support across stable and handling
  limit roles;
- collision-mitigation rows keep collision-heavy unavoidable cases in the
  panel without letting them dominate;
- mitigation-metric rows are carried as diagnostic-only rows, not ranking rows.

The quota design uses only `80 / 184` supported sources, leaving slack for
implementation failures without needing to touch unsupported rows.

## Representative Cell Rules

M1986 should select one accepted cell per selected source:

```text
stable_aeb:
  choose max threshold_score, then farther obstacle_distance, then smaller
  obstacle_half_width.

stable_aes_only:
  choose minimum threshold_score, then closer obstacle_distance, then larger
  obstacle_half_width.

drift_required_recovery:
  choose minimum threshold_score, then closer obstacle_distance, then larger
  obstacle_half_width.

unavoidable_mitigation:
  choose closer obstacle_distance, then larger obstacle_half_width, then
  minimum threshold_score.

mitigation_metric_isolation:
  use the same unavoidable/drift role rule but mark
  diagnostic_only_no_ranking_claim = true.
```

These rules are source-quality rules, not controller-family tuning. They use
source labels and accepted cells from no-rollout scenario classification only.

## Output Schema

M1986 should write:

```text
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/summary.json
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/selected_source_rows.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/selected_accepted_cells.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/profile_artifacts.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/materialization_failures.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/repair_axis_aggregate.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/role_surface_aggregate.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/claim_boundary.csv
```

Each executable spec must preserve:

```text
task_source_id
candidate_source_id
repair_candidate_id
repair_axis
repair_source_kind
source_role_semantics
feasibility_tier_id
parent_feasibility_tier_id
normalized_surface_variant
source_split
sampled_obstacle_label
speed_ref
mu
friction_step_enabled
friction_step_at
obstacle_distance
obstacle_half_width
post_obstacle_track_width
base_geometry_source
representative_cell_rule
diagnostic_only_no_ranking_claim
env_config
contract_checks
```

## Contract Checks

M1986 should preserve the current human-view actor contract:

```text
history_length == 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
```

Any contract violation should fail the materialization preflight.

## Pass Gates

M1986 should pass only if:

```text
result_class == task_quality_calibrated_outcome_support_materialization_preflight_pass
selected_source_count == 80
executable_task_spec_count == 80
planned_workload_rows == 960
profile_count == 12
selected_unsupported_source_count == 0
materialization_failure_count == 0
duplicate_task_source_id_count == 0
contract_violation_count == 0

repair_axis_selected_counts:
  offtrack_anchor_relief == 24
  offtrack_boundary_relief_extension == 16
  success_support_expansion == 20
  collision_mitigation_relief == 12
  mitigation_metric_isolation == 8

diagnostic_only_no_ranking_claim_count == 8
labels_enter_actor_input_count == 0
v2_ranking_admissible_by_default_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0

environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If M1986 fails, M1987 should audit the failure before any quota weakening or
source repair.

## Command

M1986 should run:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_outcome_support_materialization_preflight \
  --source-rows runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv \
  --accepted-cells runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight \
  --next-blocker m1987-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-result-audit
```

## Supported Claims

M1985 supports:

- a bounded materialization subset can be specified from M1983 supported source
  rows;
- the first materialization should use `80` selected sources and `960` planned
  workload rows;
- unsupported rows and diagnostic-only rows have explicit handling.

M1985 does not support:

- materialization pass;
- reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1986-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-implementation
```

M1986 should implement and run the no-reset materialization preflight.
