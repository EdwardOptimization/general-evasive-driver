# M2001 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured-Runner Quota Parameterization Implementation Audit

- status: completed
- decision: `task_quality_calibrated_outcome_support_measured_runner_quota_parameterization_audit_admit_measured_execution_command_design`
- audited implementation: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- audited tests: `tests/test_executable_v2_task_quality_calibrated_measured_runner.py`
- real 960-row measured execution in M2001: `false`
- environment rollout in M2001: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2000 is a clean focused infrastructure repair.

The calibrated measured runner now computes expected quota counts from the
active workload by default:

```text
expected_quota_source: workload
expected_source_kind_counts: count(workload.repair_source_kind)
expected_role_surface_counts: count(workload.repair_source_kind,
                                    workload.source_role_semantics,
                                    workload.normalized_surface_variant)
```

The runner writes:

```text
quota_metadata_missing_rows.csv
quota_metadata_missing_count
```

The measured execution pass gate requires:

```text
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
```

This preserves the measured-runner quota gate while removing the stale
historical constant default that blocked the M1986 repaired outcome-support
workload.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_measured_runner.py
```

Result:

```text
4 passed
```

Additional validation already passed in M2000:

```text
python -m compileall -q src tests
make research-review RESEARCH_MANIFEST=experiments/manifests/m2000-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-implementation.json
make research-validate
scripts/hooks/pre-commit
```

## Supported Claims

M2001 supports:

- measured-runner expected quotas are now artifact-driven from active workload
  rows by default;
- missing workload quota metadata fails closed and is materialized as an
  explicit artifact;
- the focused implementation is ready for a measured execution command-design
  milestone.

M2001 does not support:

- real measured execution success;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next Route

Decision:

```text
admit_measured_execution_command_design
```

Next milestone:

```text
m2002-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-command-design
```

M2002 should freeze the exact 960-row measured execution rerun command over the
M1986 repaired outcome-support artifacts in a fresh output directory. M2002
must not run the measured execution.
