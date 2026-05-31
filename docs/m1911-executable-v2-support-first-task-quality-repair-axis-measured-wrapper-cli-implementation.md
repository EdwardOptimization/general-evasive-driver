# M1911 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper CLI Implementation

- status: completed
- decision: `task_quality_repair_axis_measured_wrapper_cli_implementation_pass_admit_execution`
- branch: `paper_route_repair_axis_measured_wrapper`
- parent command design: `docs/m1910-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-command-design.md`
- source: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py`
- tests: `tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py`
- focused tests: `8 passed`
- real M1902 workload run: `false`
- environment reset/rollout/measured execution in M1911: `false`
- mocked measured CLI test: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M1911 implements the measured-wrapper CLI mode designed in M1910.

New CLI behavior:

```text
default:
  dry-run/preflight path remains active.

--measured-execution:
  loads the repair-axis matrix and source episode rows;
  builds a measured rollout function from base measured executable specs;
  calls measured_prepare_execution;
  writes measured artifacts.
```

New implementation pieces:

- `--measured-execution`
- `--base-measured-specs`
- `--device`
- `load_base_measured_specs`
- `apply_axis_geometry_delta_to_env_config`
- `build_measured_rollout_fn`

The measured rollout function loads base support-first executable specs from
the M1875 adapter output, overlays the M1902 axis task ids, applies explicit
geometry deltas, lazily loads profile checkpoints, and calls the existing
controller-family `run_workload_cell` path. The focused tests monkeypatch this
runner boundary, so M1911 itself does not run the real M1902 workload.

## Geometry Delta Mapping

The CLI binding maps only explicit task-quality geometry fields:

```text
max_steps_multiplier -> env_config.max_steps
track_width_multiplier / pre_obstacle_track_width_multiplier /
  post_obstacle_track_width_multiplier -> env_config.track_width
obstacle_clearance_gap_delta_m -> env_config.obstacle.safety_margin
obstacle_reaction_distance_delta_m -> env_config.obstacle.distance_range
```

Unknown or purely diagnostic metadata is not turned into actor input and does
not change controller profiles.

## Test Evidence

Command:

```bash
PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py
```

Result:

```text
8 passed in 0.91s
```

The focused tests verify:

- existing dry-run helper behavior;
- measured rollout extension behavior;
- default CLI dry-run behavior;
- `--measured-execution` CLI behavior with an injected mock rollout;
- explicit geometry-delta mapping.

## Supported Claims

Supported:

- the M1910 measured command now has a CLI mode;
- dry-run CLI behavior remains intact;
- the measured CLI can write expected measured artifacts under mocked rollout;
- real measured execution is now admitted as the next milestone.

Unsupported:

- real M1902 measured execution has succeeded;
- task-quality repair has improved outcomes;
- controller-family ranking;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1912-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution
```

M1912 should run the exact M1910/M1911 command over the real M1902 matrix and
defer interpretation to a later audit.
