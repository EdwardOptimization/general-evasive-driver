# M1966 Executable V2 Task-Quality Calibrated Measured Execution

- status: completed
- decision: `task_quality_calibrated_measured_execution_validation_fail_route_to_audit`
- result class: `task_quality_calibrated_measured_execution_incomplete_or_fail`
- run dir: `runs/m1966_executable_v2_task_quality_calibrated_measured_execution`
- command return code: `0`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1966 ran the command admitted by M1965:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_measured_runner \
  --executable-task-specs runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json \
  --workload runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv \
  --output-dir runs/m1966_executable_v2_task_quality_calibrated_measured_execution \
  --eval-seed-base 196500 \
  --device cpu \
  --target-episode-count 960 \
  --target-spec-count 80 \
  --target-profile-count 12 \
  --next-blocker m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit
```

## Result

The runner failed closed during validation before environment rollout:

```text
result_class: task_quality_calibrated_measured_execution_incomplete_or_fail
episode_count: 0
target_episode_count: 960
spec_count: 0
target_spec_count: 80
profile_count: 0
target_profile_count: 12
failure_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
source_kind_quota_pass: false
role_surface_quota_pass: false
```

The direct validation artifact reports:

```text
error_type: missing_spec_field
error_message: parent_feasibility_tier_id
validation_failure_rows: 8 unique task sources
```

The failing rows are all offtrack-boundary-relief task sources:

```text
tqcm_exec_v0_0056_otsr_v0_0114_offtrack_boundary_relief
tqcm_exec_v0_0057_otsr_v0_0118_offtrack_boundary_relief
tqcm_exec_v0_0058_otsr_v0_0121_offtrack_boundary_relief
tqcm_exec_v0_0059_otsr_v0_0127_offtrack_boundary_relief
tqcm_exec_v0_0060_otsr_v0_0130_offtrack_boundary_relief
tqcm_exec_v0_0061_otsr_v0_0133_offtrack_boundary_relief
tqcm_exec_v0_0062_otsr_v0_0139_offtrack_boundary_relief
tqcm_exec_v0_0063_otsr_v0_0142_offtrack_boundary_relief
```

The planned workload contains `96` affected profile workload cells because each
of the `8` task sources is crossed with `12` controller profiles.

## Artifacts

Written artifacts:

```text
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/summary.json
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/failure_rows.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/validation_failure_rows.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/metric_completeness_failures.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/profile_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/source_kind_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/role_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/normalized_surface_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/role_surface_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/sampled_label_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/outcome_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/termination_reason_aggregate.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/claim_boundary.csv
runs/m1966_executable_v2_task_quality_calibrated_measured_execution/run_state.json
```

No `episode_rows.csv` artifact was produced because no rollout started.

## Interpretation Boundary

Supported by M1966:

- the calibrated measured runner fails closed on missing required workload
  metadata before any rollout;
- the failure is localized to the offtrack-boundary-relief workload metadata
  slice;
- no training, replay, PPO, ranking, paper-level, or level3 self-ID claim was
  made.

Unsupported by M1966:

- measured rollout success;
- controller-family ranking;
- policy performance comparison;
- paper-level benchmark evidence;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Next milestone:

```text
m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit
```

M1967 must audit whether this is a workload materialization metadata bug, runner
validation overreach, or legitimate source-schema gap. It must not repair or
rerun before classifying the failure.
