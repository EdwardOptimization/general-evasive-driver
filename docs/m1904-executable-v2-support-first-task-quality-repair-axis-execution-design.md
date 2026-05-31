# M1904 Executable V2 Support-First Task-Quality Repair-Axis Execution Design

- status: completed
- decision: `task_quality_repair_axis_execution_design_admit_wrapper_implementation`
- parent audit: `docs/m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit.md`
- matrix: `runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv`
- no rollout in M1904: true
- measured execution in M1904: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Purpose

M1904 designs the wrapper/protocol needed to execute the M1902 repair-axis
matrix. This is intentionally still pre-execution. The design defines row
splits, metadata preservation, import/postprocess joins, output artifacts, and
pass gates before any environment reset or rollout.

## Parent Evidence

M1902/M1903 provide a clean no-rollout matrix:

```text
source specs: 16
controller profiles: 12
role surfaces: 8
repair-axis variants: 8
total matrix rows: 1536
original_retained rows: 192
geometry rollout rows: 960
import/postprocess rows: 576
duplicate axis keys: 0
guardrail violations: 0
```

The matrix deliberately separates three row classes:

```text
rollout_geometry_variant:
  post_clearance_recovery_window_plus: 192
  post_obstacle_containment_corridor_plus: 192
  post_clearance_recovery_corridor_combo: 192
  contained_clearance_gap_plus: 192
  contained_reaction_distance_plus: 192

import_existing_episode:
  original_retained: 192

postprocess_existing_episode:
  role_semantics_only: 192
  mitigation_scored_semantics: 192
```

Only the `rollout_geometry_variant` rows should run new environment rollouts.
The remaining rows must be imported or postprocessed from the M1895 source
episode rows and merged into the final panel.

## Compatibility Decision

The old repaired bounded-smoke runner should not be used directly because it
expects the older M1889 repaired workload schema and only three broad geometry
variants. The M1902 matrix has new axis fields and five geometry variants:

```text
task_quality_axis_id
repair_axis_variant_id
axis_applicability
target_conflict_class
target_near_miss_class
source_conflict_class
source_near_miss_flags
geometry_delta_json
semantics_delta_json
```

However, the old runner's lower-level one-cell execution helpers and aggregate
patterns are reusable. The new wrapper should own M1902-specific loaders, row
splitting, import/postprocess joins, metadata preservation, and axis aggregates.

## Required Wrapper

M1905 should implement, without running the real M1902 workload:

```text
src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py
tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py
```

The future execution command should load:

```text
--task-quality-repair-axis-matrix \
  runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv
--task-quality-repair-axis-spec \
  runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_spec.json
--source-episode-rows \
  runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv
--m1674-run-dir \
  runs/m1674_controller_family_one_seed_public_pilot
--eval-seed-base 190500
--device cpu
--output-dir runs/m1905_executable_v2_support_first_task_quality_repair_axis_execution
--no-resume
--next-blocker m1906-executable-v2-support-first-task-quality-repair-axis-execution-command-design
```

M1905 should only implement the wrapper and focused tests. It must not execute
the real M1902 matrix.

## Execution Protocol

### Rollout Rows

The wrapper should execute only:

```text
execution_row_kind == rollout_geometry_variant
target rollout count == 960
```

For each rollout row, the wrapper should:

- parse `geometry_delta_json` and validate it against a whitelist;
- build an executable task config from the base support-first spec plus the
  declared geometry delta;
- preserve `profile_name == controller_profile_name`;
- use the controller config/checkpoint named in the row;
- append one row to `rollout_episode_rows.csv`;
- preserve all axis, source, role, surface, hidden-dynamics, obstacle, profile,
  and provenance metadata;
- set row-level execution provenance to indicate new rollout;
- keep training/replay/PPO/promoted/private-holdout/profile-tuning/ranking
  guardrails false.

### Import/Postprocess Rows

The wrapper should import or postprocess:

```text
execution_row_kind in {import_existing_episode, postprocess_existing_episode}
target count == 576
```

For each row it should:

- join `source_episode_workload_id` against M1895 `episode_rows.csv`;
- copy source rollout metrics from the matched source row;
- overwrite metadata with M1902 axis metadata;
- set row-level provenance to `import_existing_episode` or
  `postprocess_existing_episode`;
- recompute only diagnostic fields that are pure functions of existing metrics;
- avoid creating fake rollout metrics;
- keep `environment_rollout_started` false for imported/postprocessed rows.

For `role_semantics_only` and `mitigation_scored_semantics`, the wrapper may
add diagnostic outcome columns such as:

```text
obstacle_clearance_pass
road_containment_pass
offtrack_after_clearance
contained_collision
near_containment_after_clearance
near_clearance_with_containment
mitigation_impact_severity_proxy
bounded_departure_proxy
```

These are metric outputs only and must not enter actor observations.

## Required Metadata

Every combined-panel row must preserve:

```text
task_quality_repair_axis_row_id
task_quality_axis_id
repair_axis_variant_id
axis_applicability
target_conflict_class
target_near_miss_class
target_role_surface_id
source_conflict_class
source_near_miss_flags
source_episode_workload_id
base_task_source_id
base_support_first_workload_id
axis_task_source_id
axis_workload_id
support_first_workload_id
task_source_id
support_first_v2_panel_spec_id
source_scenario_spec_id
controller_profile_name
profile_name
scenario_profile_name
role_panel_id
v2_role_surface_id
surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
geometry_delta_json
semantics_delta_json
execution_row_kind
row_provenance
profile_config_path
checkpoint_path
eval_seed
```

The row must also keep:

```text
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Required Output Artifacts

A later execution should write:

```text
summary.json
episode_rows.csv
rollout_episode_rows.csv
import_postprocess_episode_rows.csv
failure_rows.csv
import_postprocess_failure_rows.csv
run_state.json
task_quality_axis_aggregate.csv
repair_axis_variant_aggregate.csv
axis_applicability_aggregate.csv
execution_row_kind_aggregate.csv
role_surface_axis_aggregate.csv
role_surface_axis_variant_aggregate.csv
controller_profile_axis_variant_aggregate.csv
axis_conflict_class_aggregate.csv
axis_near_miss_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
import_postprocess_alignment.csv
```

`episode_rows.csv` is the combined `1536`-row panel. Separate rollout and
import/postprocess files keep provenance auditable.

## Required Pass Criteria For Later Execution

A later execution should pass only if:

```text
rollout_episode_count == 960
import_postprocess_episode_count == 576
total_panel_row_count == 1536
failure_count == 0
import_postprocess_failure_count == 0
controller_profile_count == 12
source_spec_count == 16
repair_axis_variant_count == 8
role_surface_count == 8
axis metadata completeness == true
metric completeness passed == true
guardrail violation count == 0
controller-family ranking claim made == false
paper-level claim made == false
level3 self-ID claim made == false
```

Even if execution passes, interpretation must be deferred to a result audit.
Controller-family ranking remains blocked until a later audit confirms that
joint clearance/containment and mitigation semantics are interpretable.

## Next Step

Route to:

```text
m1905-executable-v2-support-first-task-quality-repair-axis-wrapper-implementation
```

M1905 should implement the wrapper and focused tests only. It must not run the
real M1902 workload, environment reset, rollout, measured execution, training,
replay, PPO, private holdout, controller ranking, paper-level claims, or level3
self-ID claims.

## Claim Boundary

Supported:

- M1902 has a clean matrix that can be made executable with a dedicated wrapper;
- the wrapper must run only geometry rows and import/postprocess the rest;
- ranking remains blocked until execution and post-execution audit.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
