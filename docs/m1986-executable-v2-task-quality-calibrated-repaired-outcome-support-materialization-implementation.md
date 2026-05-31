# M1986 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Materialization Implementation

- status: completed
- decision: `task_quality_calibrated_outcome_support_materialization_preflight_pass_route_to_result_audit`
- result class: `task_quality_calibrated_outcome_support_materialization_preflight_pass`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_outcome_support_materialization_preflight.py`
- focused tests: `3 passed`
- summary: `runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/summary.json`
- materialization preflight: `true`
- reset/rollout/measured execution: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight.py
```

Result:

```text
3 passed
```

No-reset materialization preflight:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_outcome_support_materialization_preflight \
  --source-rows runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv \
  --accepted-cells runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight \
  --next-blocker m1987-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-result-audit
```

Return code:

```text
0
```

## Result

M1986 passes the M1985 materialization preflight gates:

```text
result_class: task_quality_calibrated_outcome_support_materialization_preflight_pass
input_source_row_count: 192
input_accepted_cell_row_count: 8358
eligible_source_count: 184
selected_source_count: 80
executable_task_spec_count: 80
profile_count: 12
planned_workload_rows: 960
selected_unsupported_source_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_key_count: 0
forbidden_key_violation_count: 0
contract_violation_count: 0
missing_profile_artifact_count: 0
guardrail_violation_count: 0
```

Repair-axis selected quotas match M1985:

```text
offtrack_anchor_relief: 24
offtrack_boundary_relief_extension: 16
success_support_expansion: 20
collision_mitigation_relief: 12
mitigation_metric_isolation: 8
```

Diagnostic-only handling:

```text
diagnostic_only_no_ranking_claim_count: 8
```

The generated executable specs preserve the human-view/no-wheel contract:

```text
history_length == 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
```

## Artifacts

M1986 wrote:

```text
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/summary.json
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/selected_source_rows.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/selected_accepted_cells.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/planned_workload.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/profile_artifacts.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/materialization_failures.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/repair_axis_aggregate.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/role_surface_aggregate.csv
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/claim_boundary.csv
```

## Supported Claims

M1986 supports:

- the M1985 bounded materialization subset can be converted into `80`
  executable task specs;
- the resulting planned workload has `960` rows across `12` controller
  profiles;
- unsupported M1983 source rows were excluded;
- diagnostic-only mitigation rows are marked and not ranking rows;
- the generated env configs pass the human-view/no-wheel contract checks.

M1986 does not support:

- reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1987-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-result-audit
```

M1987 should audit the materialization result before reset validation command
design.
