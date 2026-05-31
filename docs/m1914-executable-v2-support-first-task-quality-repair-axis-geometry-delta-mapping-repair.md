# M1914 Executable V2 Support-First Task-Quality Repair-Axis Geometry-Delta Mapping Repair

- status: completed
- decision: `geometry_delta_mapping_repair_pass_admit_measured_rerun`
- branch: `paper_route_repair_axis_measured_wrapper`
- parent audit: `docs/m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit.md`
- source: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py`
- tests: `tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py`
- focused tests: `9 passed`
- real M1902 workload run: `false`
- environment reset/rollout/measured execution in M1914: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Repair

M1914 repairs the failure mechanism identified in M1913.

Rule now implemented:

```text
If geometry_delta_json has road_geometry_fixed=true,
do not apply obstacle_clearance_gap_delta_m or
obstacle_reaction_distance_delta_m to env_config.obstacle.
Keep those fields as task-quality/postprocess metadata.
```

The existing explicit mappings for non-fixed geometry remain tested:

```text
max_steps_multiplier -> env_config.max_steps
track_width_multiplier / pre_obstacle_track_width_multiplier /
  post_obstacle_track_width_multiplier -> env_config.track_width
obstacle_clearance_gap_delta_m -> env_config.obstacle.safety_margin
obstacle_reaction_distance_delta_m -> env_config.obstacle.distance_range
```

## Test Evidence

Command:

```bash
PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py
```

Result:

```text
9 passed in 2.10s
```

New test coverage:

- non-fixed obstacle deltas still mutate the explicit env fields;
- `road_geometry_fixed=true` obstacle deltas no longer mutate obstacle
  `safety_margin` or `distance_range`;
- dry-run and measured CLI tests still pass.

## Supported Claims

Supported:

- M1912's localized sampling-failure mechanism has a focused code repair;
- the repair does not change actor inputs or controller profiles;
- a measured execution rerun is now admissible.

Unsupported:

- M1912 has been repaired in measured data;
- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun
```

M1915 should rerun the measured wrapper command in a fresh output directory
using the same `eval-seed-base` as M1912 to isolate the mapping repair.
