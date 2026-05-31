# M1958 Executable V2 Task-Quality Calibrated Materialization Preflight Implementation

- status: completed
- decision: `task_quality_calibrated_materialization_preflight_pass_route_to_reset_command_design`
- branch: `paper_route_task_quality_calibrated_materialization`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_materialization_preflight.py`
- focused tests: `2 passed`
- summary: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json`
- executable specs: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv`
- reset/rollout/measured execution in M1958: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M1958 implements and runs the focused no-reset preflight adapter over the real
M1956/M1952 artifacts:

```text
result_class: task_quality_calibrated_materialization_preflight_pass
selected_source_count: 80
executable_task_spec_count: 80
controller_profile_count: 12
planned_workload_cell_count: 960
input_accepted_cell_row_count: 5981
selected_accepted_cell_row_count: 3382
missing_accepted_cell_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_key_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
missing_profile_artifact_count: 0
guardrail_violation_count: 0
```

Preserved source-kind counts:

```text
anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

Calibrated-anchor provenance:

```text
calibrated_anchor_selected_count: 32
post_friction_step: 16
steady_surface: 16
```

## Artifacts

M1958 writes:

```text
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/profile_artifacts.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/materialization_failures.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/source_kind_aggregate.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/role_surface_aggregate.csv
runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/claim_boundary.csv
```

## Interpretation Boundary

Supported by M1958:

- the M1956 calibrated source subset can be converted into executable task
  specs without reset;
- the planned 80 x 12 = 960 workload is materialized with complete profile
  artifacts;
- human-view contract checks, forbidden-key checks, and guardrails pass at
  preflight level.

Unsupported by M1958:

- environment reset validity;
- rollout or measured execution success;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1959-executable-v2-task-quality-calibrated-reset-validation-command-design
```

M1959 should design the exact reset-only command. Because the generic M1933
validator can reset env configs but does not preserve all calibrated repair
metadata in reset rows, M1959 should decide whether to wrap or extend it before
any reset execution.
