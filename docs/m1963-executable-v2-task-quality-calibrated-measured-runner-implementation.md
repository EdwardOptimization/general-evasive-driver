# M1963 Executable V2 Task-Quality Calibrated Measured Runner Implementation

- status: completed
- decision: `task_quality_calibrated_measured_runner_adapter_pass_admit_command_design`
- branch: `paper_route_task_quality_calibrated_materialization`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- focused tests: `3 passed`
- real rollout/measured execution in M1963: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M1963 implements the focused calibrated measured-runner adapter required by
M1962. The adapter preserves calibrated repair metadata as first-class episode,
failure, and aggregate fields:

```text
repair_source_kind
selection_quota_name
source_role_semantics
parent_feasibility_tier_id
parent_surface_variant
normalized_surface_variant
base_geometry_source
representative_cell_rule
profile_name
profile_config_path
checkpoint_path
```

Focused mocked tests cover:

- successful synthetic measured execution with metadata and aggregates;
- rollout failure preservation with calibrated metadata;
- fail-closed schema mismatch behavior.

M1963 does not run the real M1958 960-cell workload.

## Implemented Artifacts

```text
src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py
tests/test_executable_v2_task_quality_calibrated_measured_runner.py
```

The runner can later execute:

```text
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
```

with target counts:

```text
episode_count: 960
spec_count: 80
profile_count: 12
```

## Interpretation Boundary

Supported by M1963:

- a calibrated metadata-preserving measured runner exists;
- synthetic execution tests pass;
- real measured execution can be command-designed next.

Unsupported by M1963:

- real rollout success;
- measured controller performance;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1964-executable-v2-task-quality-calibrated-measured-execution-command-design
```

M1964 should freeze the exact real measured execution command and pass gates.
It must not run the workload.
