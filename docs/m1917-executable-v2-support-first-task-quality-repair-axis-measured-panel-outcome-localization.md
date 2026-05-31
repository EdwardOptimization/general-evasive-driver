# M1917 Executable V2 Support-First Task-Quality Repair-Axis Measured Panel Outcome Localization

- status: completed
- decision: `task_quality_repair_axis_measured_panel_outcome_localization_pass_route_to_branch_synthesis`
- result class: `task_quality_repair_axis_measured_panel_outcome_localization_pass`
- summary: `runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization/summary.json`
- conflict rows: `runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization/conflict_class_rows.csv`
- source episode rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/episode_rows.csv`
- implementation: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_outcome_localization.py`
- focused tests: `2 passed`
- reset/rollout/measured execution in M1917: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_outcome_localization \
  --episode-rows runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/episode_rows.csv \
  --output-dir runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization
```

Return code:

```text
0
```

## Localization Coverage

M1917 classified all rows without rerun:

```text
episode rows: 1536 / 1536
all selected metrics finite: true
all rows classified once: true
guardrail violations: 0
```

Classification sources:

```text
explicit_task_quality_fields: 576
raw_metric_inference: 960
```

The `960` raw-inference rows are the newly measured geometry variants from
M1915. Their task-quality flags are inferred from raw measured metrics:

```text
obstacle_clearance_pass := collision is false and min_clearance_margin > 0
road_containment_pass := termination_reason != off_track
collision_failure := collision
```

## Conflict Surface

Full-panel conflict counts:

```text
joint_clearance_containment: 0
clearance_only_offtrack: 1257
containment_collision: 261
collision_and_offtrack: 18
other_non_success: 0
```

Near-miss counts:

```text
near_containment_after_clearance: 457
near_clearance_with_containment: 165
late_offtrack_after_clearance: 66
near_miss_rows: 644
```

Execution-kind split:

```text
import_existing_episode:
  clearance_only_offtrack: 160
  containment_collision: 30
  collision_and_offtrack: 2

postprocess_existing_episode:
  clearance_only_offtrack: 320
  containment_collision: 60
  collision_and_offtrack: 4

rollout_geometry_variant:
  clearance_only_offtrack: 777
  containment_collision: 171
  collision_and_offtrack: 12
```

Across repair-axis variants, no variant creates a joint
clearance-and-containment row. The conflict remains a broad split between
obstacle clearance with road departure and road containment until collision.
Variant-level rates are diagnostic task-quality evidence only, not
controller-family ranking.

## Decision

M1917 passes as a no-rerun localization artifact and supports these claims:

- M1915's complete panel can be classified consistently;
- the M1912/M1915 execution infrastructure is no longer the blocker;
- the task-quality repair-axis branch still has zero joint
  clearance-containment rows;
- there are substantial near-miss rows, so the branch produced useful
  scenario/task-quality information;
- the next step should be branch synthesis, not another local repair loop.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1918-executable-v2-support-first-task-quality-repair-axis-measured-branch-synthesis
```

M1918 should synthesize M1909-M1917 and decide whether to stop this measured
repair-axis branch, pivot to a broader task-quality/scenario design branch, or
continue only with a clearly justified non-local evidence expansion.
