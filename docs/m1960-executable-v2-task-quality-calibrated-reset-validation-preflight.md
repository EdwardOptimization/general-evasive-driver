# M1960 Executable V2 Task-Quality Calibrated Reset Validation Preflight

- status: completed
- decision: `task_quality_calibrated_reset_validation_pass_route_to_result_audit`
- branch: `paper_route_task_quality_calibrated_materialization`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_reset_validation_preflight.py`
- focused tests: `2 passed`
- summary: `runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json`
- reset execution in M1960: `true`
- rollout/measured execution in M1960: `false`
- policy action executed: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M1960 runs the frozen reset-only validation command over the M1958 calibrated
80-spec panel:

```text
result_class: task_quality_calibrated_reset_validation_preflight_pass
input_executable_spec_count: 80
target_executable_spec_count: 80
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
contract_violation_count: 0
label_actor_input_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Source-kind and role/surface quotas remain intact:

```text
source_kind_quota_pass: true
role_surface_quota_pass: true

anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

Sampled labels:

```text
aeb_feasible: 44
aes_feasible: 14
drift_required: 9
unavoidable: 13
```

## Artifacts

M1960 writes:

```text
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_failure_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/contract_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_distribution_by_role_surface.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/claim_boundary.csv
```

## Interpretation Boundary

Supported by M1960:

- the M1958 calibrated 80-spec public diagnostic panel is reset-valid under the
  current simulator;
- strict human-view observation contract checks pass at reset;
- calibrated repair metadata is preserved through reset rows and aggregates.

Unsupported by M1960:

- rollout success;
- measured execution success;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit
```

M1961 should audit this reset pass before any measured execution command design
or controller comparison.
