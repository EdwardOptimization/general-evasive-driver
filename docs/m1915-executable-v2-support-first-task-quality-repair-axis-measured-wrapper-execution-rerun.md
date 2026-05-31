# M1915 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Execution Rerun

- status: completed
- decision: `task_quality_repair_axis_measured_wrapper_execution_rerun_pass_route_to_result_audit`
- result class: `task_quality_repair_axis_measured_wrapper_execution_pass`
- summary: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json`
- episode rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/episode_rows.csv`
- rollout rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/rollout_episode_rows.csv`
- import/postprocess rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/import_postprocess_episode_rows.csv`
- failure rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/failure_rows.csv`
- command eval seed base: `191200`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_execution \
  --task-quality-repair-axis-matrix runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv \
  --source-episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --output-dir runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun \
  --eval-seed-base 191200 \
  --measured-execution
```

Return code:

```text
0
```

## Target Counts

M1915 reran the repaired measured-wrapper command in a fresh output directory
after M1914's `road_geometry_fixed=true` obstacle-delta mapping repair.

```text
matrix rows: 1536
planned rollout rows: 960
measured rollout rows: 960
import/postprocess rows: 576
combined panel rows: 1536
failure rows: 0
guardrail violations: 0
```

Execution row kinds:

```text
rollout_geometry_variant: 960
import_existing_episode: 192
postprocess_existing_episode: 384
```

Repair-axis variant counts:

```text
contained_clearance_gap_plus: 192
contained_reaction_distance_plus: 192
mitigation_scored_semantics: 192
original_retained: 192
post_clearance_recovery_corridor_combo: 192
post_clearance_recovery_window_plus: 192
post_obstacle_containment_corridor_plus: 192
role_semantics_only: 192
```

Task-quality axis counts:

```text
baseline_and_semantics_retention: 384
contained_collision_clearance_feasibility: 384
post_clearance_containment_recovery: 576
unavoidable_mitigation_semantics: 192
```

## Interpretation Boundary

M1915 supports only this execution claim:

```text
The repaired measured-wrapper command now completes the registered
1536-row task-quality repair-axis panel with clean guardrails.
```

It does not support:

- controller-family ranking;
- task-quality repair success;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

The `summary.json` still carries the older `next_blocker` string from the
measured-wrapper helper. The governing route is this milestone document and the
manifest/status files: M1915 routes to a result audit.

## Next

Next milestone:

```text
m1916-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-rerun-result-audit
```

M1916 should audit the complete M1915 panel before any controller-family
ranking, paper-level result, training, replay, PPO, or level3 self-ID claim.
