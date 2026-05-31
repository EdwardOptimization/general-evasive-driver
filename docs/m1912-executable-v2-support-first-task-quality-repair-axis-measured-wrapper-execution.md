# M1912 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Execution

- status: completed
- decision: `task_quality_repair_axis_measured_wrapper_execution_incomplete_route_to_failure_audit`
- result class: `task_quality_repair_axis_measured_wrapper_execution_needs_repair`
- summary: `runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/summary.json`
- return code: `2`
- real measured execution attempted: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_execution \
  --task-quality-repair-axis-matrix runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv \
  --source-episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --output-dir runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution \
  --eval-seed-base 191200 \
  --measured-execution
```

## Result

```text
matrix_row_count: 1536
planned_rollout_row_count: 960
measured_rollout_row_count: 768
target_measured_rollout_row_count: 960
import_postprocess_row_count: 576
combined_panel_row_count: 1344
target_combined_panel_row_count: 1536
failure_count: 192
guardrail_violation_count: 0
```

The command did not pass M1912 gates because `192` rollout rows failed before
measurement could be written.

Failure localization:

```text
error_type:
  RuntimeError: 192

dominant error:
  failed to sample an obstacle scenario matching the configured filters

task_quality_axis_id:
  contained_collision_clearance_feasibility: 192

repair_axis_variant_id:
  contained_reaction_distance_plus: 108
  contained_clearance_gap_plus: 84

target_conflict_class:
  containment_collision: 192
```

Completed rollout rows:

```text
post_clearance_recovery_window_plus: 192
post_obstacle_containment_corridor_plus: 192
post_clearance_recovery_corridor_combo: 192
contained_clearance_gap_plus: 108
contained_reaction_distance_plus: 84
```

## Interpretation Boundary

This is execution/failure evidence, not controller ranking evidence. Completed
rows should not be used for controller comparison or paper claims before a
failure audit and any required repair.

## Supported Claims

Supported:

- the measured-wrapper CLI can execute real rollout rows and merge imports;
- post-clearance containment/recovery variants executed completely;
- current contained-collision feasibility mapping is not execution-complete;
- guardrails and claim boundaries remained clean.

Unsupported:

- M1912 pass;
- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Failure Classification

Preliminary failure type:

```text
scenario_sampling_failure
```

The likely failure surface is the contained-collision feasibility geometry
mapping. Rows with `road_geometry_fixed=true` and obstacle clearance/reaction
deltas should be audited before another execution.

## Next

Next milestone:

```text
m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit
```

M1913 should audit whether these failures are caused by the M1911 geometry
delta mapping, by infeasible source scenarios, or by a genuine task-quality
spec issue. It should not rerun execution.
