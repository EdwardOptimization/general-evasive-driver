# M2000 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured-Runner Quota Parameterization Implementation

- status: completed
- decision: `task_quality_calibrated_outcome_support_measured_runner_quota_parameterization_implementation_pass_route_to_audit`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- focused tests: `4 passed`
- real 960-row measured execution in M2000: `false`
- environment rollout in M2000: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Change

M2000 implements the measured-runner quota repair designed in M1998 and admitted
by M1999 synthesis.

The calibrated measured runner now derives expected quota counts from the active
workload by default:

```text
expected_source_kind_counts =
  count(workload_row.repair_source_kind)

expected_role_surface_counts =
  count(
    workload_row.repair_source_kind,
    workload_row.source_role_semantics,
    workload_row.normalized_surface_variant
  )
```

The runner writes these summary fields:

```text
expected_quota_source
expected_source_kind_counts
expected_role_surface_counts
quota_metadata_missing_count
```

It also writes:

```text
quota_metadata_missing_rows.csv
```

Pass conditions now require:

```text
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
```

The default route no longer uses `expected=None` as a silent quota bypass. If
the runner cannot compute expected quota metadata from the workload, the result
remains fail-closed.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_measured_runner.py
```

Result:

```text
4 passed in 0.96s
```

The tests cover:

- non-legacy workload-derived source-kind and role-surface quotas;
- preserved metadata and aggregate artifacts;
- rollout failure preservation with workload-derived expected quota summaries;
- validation-failure summary schema;
- missing quota metadata fail-closed behavior and
  `quota_metadata_missing_rows.csv`.

## Claim Boundary

M2000 supports:

- the measured runner has focused code support for workload-derived expected
  quotas;
- missing quota metadata is represented as an explicit fail-closed artifact;
- focused fake-rollout tests pass.

M2000 does not support:

- real 960-row measured execution success;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next

Next milestone:

```text
m2001-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-parameterization-implementation-audit
```

M2001 should audit the focused implementation before any measured execution
command design or rerun.
