# M1998 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured-Runner Quota Parameterization Design

- status: completed
- decision: `task_quality_calibrated_outcome_support_measured_runner_quota_parameterization_design_route_to_required_branch_synthesis`
- code edited in M1998: `false`
- reset rerun in M1998: `false`
- rollout/measured execution in M1998: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1996 restored reset-validation evidence for the repaired outcome-support panel:

```text
reset_success_count: 80
reset_failure_count: 0
expected_quota_source: executable_task_specs
quota_metadata_missing_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
contract_violation_count: 0
guardrail_violation_count: 0
```

M1997 then blocked direct 960-row measured execution because the calibrated
measured runner still has stale historical quota constants. The M1986 workload
has:

```text
anchor_neighborhood: 288
mitigation_isolation_check: 240
offtrack_boundary_relief: 192
success_stabilizer: 240
```

The measured runner still expects the older M1958-style distribution:

```text
anchor_neighborhood: 384
mitigation_isolation_check: 192
offtrack_boundary_relief: 96
success_stabilizer: 288
```

If we run measured execution now, a clean 960-row rollout could fail the source
quota gate for the same reason M1990 failed before the reset validator repair.
The fix must not disable quota checking. It must make the expected quota source
match the active measured workload.

## Design

The next implementation milestone should repair
`src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py` with
artifact-driven measured-runner quota expectations.

### Expected Quota Source

Default expected quota source:

```text
the active planned_workload.csv loaded by the measured runner
```

The measured execution rows are one row per workload cell, so expected quotas
should be derived from workload rows, not from executable specs:

```text
expected_source_kind_counts =
  count(workload_row.repair_source_kind for workload_row in planned_workload)
```

Role-surface expectations should use the same workload rows:

```text
expected_role_surface_counts =
  count(
    workload_row.repair_source_kind,
    workload_row.source_role_semantics,
    workload_row.normalized_surface_variant
  )
```

Then measured episode rows must match these expected counts exactly:

```text
source_kind_quota_pass =
  observed_episode_source_kind_counts == expected_source_kind_counts

role_surface_quota_pass =
  observed_episode_role_surface_counts == expected_role_surface_counts
```

This preserves the purpose of the gate: measured execution must complete the
active workload without silently dropping workload cells or losing calibrated
repair metadata. The earlier materialization gates remain responsible for
checking whether the planned workload distribution itself is appropriate.

### Fail-Closed Semantics

Required non-empty metadata per workload row:

```text
repair_source_kind
source_role_semantics
normalized_surface_variant
```

New or repaired summary fields:

```text
expected_quota_source: workload
expected_source_kind_counts: {...}
expected_role_surface_counts: {...}
quota_metadata_missing_count: int
```

New artifact:

```text
quota_metadata_missing_rows.csv
```

Pass conditions must require:

```text
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
```

If the expected quota source is empty, missing required fields, or cannot be
computed, the result must remain fail-closed. `expected=None` must not be used
as a silent bypass in the default CLI/measured-runner route.

### Compatibility Boundary

This is measured-runner infrastructure only. It must not alter:

- actor inputs;
- rewards;
- dynamics;
- profile configs;
- controller-family policies;
- scenario specs;
- rollout semantics.

Older calibrated panels should still pass because expected counts will be
computed from their own planned workload. The historical constants may remain
as a legacy reference, but they should no longer be the default active gate for
new measured execution.

### Focused Tests

The implementation milestone should add tests for:

```text
1. M1986-style non-legacy workload distribution:
   expected counts are computed from workload rows, and source/role quota gates
   pass when fake rollout emits one measured episode per workload cell.

2. Missing quota metadata:
   quota_metadata_missing_count > 0, quota_metadata_missing_rows.csv is written,
   and result_class remains incomplete_or_fail.

3. Summary schema:
   expected_quota_source, expected_source_kind_counts,
   expected_role_surface_counts, and quota_metadata_missing_count are present.

4. Validation-failure path:
   expected quota fields are still emitted even when measured execution fails
   before rollout due validation failures.
```

The implementation milestone should use focused fake-rollout tests only. It
must not run the real 960-row measured execution.

## Claim Boundary

M1998 supports only:

```text
the calibrated measured runner quota gate has a bounded artifact-driven repair design.
```

M1998 does not support:

- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m1999-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-runner-quota-branch-synthesis
```

The branch has reached the 10-milestone workflow-synthesis cadence after
M1989-M1998, so M1999 must synthesize the reset/quota-readiness branch before
any implementation milestone. If M1999 chooses `continue`, the next route should
be a focused measured-runner quota implementation and tests. Real 960-row
measured execution remains blocked.
