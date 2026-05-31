# M1906 Executable V2 Support-First Task-Quality Repair-Axis Wrapper Preflight

- status: completed
- decision: `task_quality_repair_axis_wrapper_preflight_pass_route_to_result_audit`
- manifest: `experiments/manifests/m1906-executable-v2-support-first-task-quality-repair-axis-wrapper-preflight.json`
- summary: `runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/summary.json`
- reset/rollout in M1906: false
- measured execution in M1906: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_execution \
  --task-quality-repair-axis-matrix runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv \
  --source-episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --output-dir runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight \
  --eval-seed-base 190600
```

## Result

M1906 passes as a no-rollout wrapper preflight:

```text
result_class: task_quality_repair_axis_execution_wrapper_preflight_pass
matrix_row_count: 1536
planned_rollout_row_count: 960
import_postprocess_row_count: 576
combined_panel_row_count: 1536
failure_count: 0
source_spec_count: 16
controller_profile_count: 12
role_surface_count: 8
repair_axis_variant_count: 8
environment_reset_started: false
environment_rollout_started: false
measured_rollout_started: false
policy_action_executed: false
training/replay/PPO: false
ranking_blocked: true
```

Row kind counts:

```text
rollout_geometry_variant: 960
import_existing_episode: 192
postprocess_existing_episode: 384
```

Variant counts:

```text
original_retained: 192
role_semantics_only: 192
post_clearance_recovery_window_plus: 192
post_obstacle_containment_corridor_plus: 192
post_clearance_recovery_corridor_combo: 192
contained_clearance_gap_plus: 192
contained_reaction_distance_plus: 192
mitigation_scored_semantics: 192
```

## Artifacts

M1906 wrote:

```text
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/summary.json
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/planned_rollout_rows.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/import_postprocess_episode_rows.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/episode_rows.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/failure_rows.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/task_quality_axis_aggregate.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/repair_axis_variant_aggregate.csv
runs/m1906_executable_v2_support_first_task_quality_repair_axis_wrapper_preflight/execution_row_kind_aggregate.csv
```

The artifacts are preflight outputs, not measured rollout outputs. The
`planned_rollout_rows.csv` file schedules candidate geometry rows for a later
execution milestone; it does not contain executed environment results.

## Implementation Note

During M1906, the wrapper default `next_blocker` was corrected to route to a
preflight result audit before execution command design. The preflight was rerun
after that correction.

## Decision

Route to:

```text
m1907-executable-v2-support-first-task-quality-repair-axis-wrapper-preflight-result-audit
```

M1907 must audit the preflight artifacts before any measured execution command
design. Direct rollout, controller ranking, training, PPO, paper-level claims,
and level3 self-ID claims remain blocked.

## Claim Boundary

Supported:

- wrapper preflight count and join gates passed on the real M1902 matrix;
- no rollout or policy action was executed;
- controller ranking remains blocked.

Unsupported:

- measured execution readiness before audit;
- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
