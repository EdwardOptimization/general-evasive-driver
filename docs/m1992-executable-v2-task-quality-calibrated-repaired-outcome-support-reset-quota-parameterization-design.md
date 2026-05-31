# M1992 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Quota Parameterization Design

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_quota_parameterization_design_admit_focused_implementation`
- code edited in M1992: `false`
- reset rerun in M1992: `false`
- rollout/measured execution in M1992: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1990 proved that all `80` M1986 executable specs reset successfully under the
strict 72-dimensional human-view contract, but the reset validator still
returned:

```text
result_class: task_quality_calibrated_reset_validation_preflight_fail
source_kind_quota_pass: false
role_surface_quota_pass: false
```

M1991 audited this as `metric_artifact`: the validator compares active reset
rows against constants from the older M1956/M1958 calibrated panel:

```text
anchor_neighborhood: 32
mitigation_isolation_check: 16
offtrack_boundary_relief: 8
success_stabilizer: 24
```

The M1986 repaired outcome-support panel intentionally has a different selected
distribution:

```text
anchor_neighborhood: 24
mitigation_isolation_check: 20
offtrack_boundary_relief: 16
success_stabilizer: 20
```

The repair must not disable quota checks. It must make the expected quota
source match the active executable panel.

## Design

M1993 should repair
`src/autodrift/executable_v2_task_quality_calibrated_reset_validation_preflight.py`
with artifact-driven quota expectations.

### Expected Quota Source

Default expected quota source:

```text
the active executable_task_specs loaded by the reset validator
```

The validator should compute expected source-kind counts from the input specs
before reset:

```text
expected_source_kind_counts =
  count(spec.repair_source_kind for spec in executable_task_specs)
```

It should compute expected role-surface counts from the same specs:

```text
expected_role_surface_counts =
  count(
    spec.repair_source_kind,
    spec.source_role_semantics,
    spec.normalized_surface_variant
  )
```

Then reset rows must match these expected counts exactly:

```text
source_kind_quota_pass =
  observed_reset_source_kind_counts == expected_source_kind_counts

role_surface_quota_pass =
  observed_reset_role_surface_counts == expected_role_surface_counts
```

This keeps the quota check meaningful: it verifies that reset validation did
not drop specs or lose calibrated metadata relative to the input executable
panel. The earlier materialization gates remain responsible for checking that
the selected panel itself had the intended repair-axis quotas.

### Fail-Closed Semantics

The repaired validator must fail if expected quota metadata is missing or
inconsistent.

Required non-empty metadata per spec:

```text
repair_source_kind
source_role_semantics
normalized_surface_variant
```

New summary fields:

```text
expected_quota_source: executable_task_specs
expected_source_kind_counts: {...}
expected_role_surface_counts: {...}
quota_metadata_missing_count: int
quota_metadata_missing_rows: artifact path or summarized count
```

Pass conditions must require:

```text
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
```

If the expected quota source is empty, missing required fields, or cannot be
computed, the result must remain fail-closed. The implementation must not use
`expected=None` as a silent bypass.

### Backward Compatibility Boundary

This is not actor compatibility and does not alter the driver. It is reset
validator compatibility only.

Old M1960/M1972 style panels should still pass because computing expected
counts from their executable specs should reproduce the old constants. The old
constants may remain as a documented legacy reference, but they should no
longer be the default active gate.

### Tests

M1993 should add focused tests for:

```text
1. M1986-style repaired outcome-support quota distribution:
   expected counts are computed from specs, source_kind_quota_pass true,
   role_surface_quota_pass true when all resets succeed.

2. Legacy calibrated distribution:
   computed expected counts match the old hard-coded distribution.

3. Missing quota metadata:
   quota_metadata_missing_count > 0 and result_class remains fail.

4. Summary schema:
   expected_quota_source, expected_source_kind_counts,
   expected_role_surface_counts, quota_metadata_missing_count are present.
```

M1993 should not rerun the real M1990 command. It should implement the repair
and run focused tests only. A later milestone should rerun the exact M1990
reset command with the repaired validator.

## Claim Boundary

M1992 supports only:

```text
the reset validator quota gate has a bounded repair design.
```

M1992 does not support:

- reset-validation pass for M1986;
- measured rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- level3 self-identification.

## Next

Next milestone:

```text
m1993-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-quota-parameterization-implementation
```

M1993 should implement the focused validator repair and tests. It must not run
the real M1990 reset command.
