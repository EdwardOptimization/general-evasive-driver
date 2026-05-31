# M1994 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Quota Parameterization Implementation Audit

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_quota_parameterization_audit_admit_repaired_reset_rerun_command_design`
- audited implementation: `src/autodrift/executable_v2_task_quality_calibrated_reset_validation_preflight.py`
- audited tests: `tests/test_executable_v2_task_quality_calibrated_reset_validation_preflight.py`
- real M1990 reset rerun in M1994: `false`
- rollout/measured execution in M1994: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M1993 is clean focused infrastructure repair.

Implementation changes audited:

```text
expected_quota_source: executable_task_specs
expected_source_kind_counts: computed from input specs
expected_role_surface_counts: computed from input specs
quota_metadata_missing_count: added to summary
quota_metadata_missing_rows.csv: added artifact
pass gate requires quota_metadata_missing_count == 0
```

Focused test result:

```text
4 passed
```

The implementation preserves the quota gate. It does not replace quota checks
with a permissive bypass. It changes the expected distribution source from a
historical hard-coded panel to the active executable spec panel, which is the
right reset-validation invariant: reset rows must preserve the active panel's
metadata exactly.

## Supported Claims

M1994 supports:

- the stale quota metric artifact from M1990 has a focused implementation
  repair;
- the repair is test-covered for repaired-panel quotas, legacy quotas, summary
  schema, and missing-metadata fail-closed behavior;
- no real reset rerun happened in M1993 or M1994;
- a repaired reset-validation rerun command design is admissible.

M1994 does not support:

- reset-validation pass for M1986 under the repaired validator;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_repaired_reset_rerun_command_design
```

M1995 should freeze the repaired reset-only command. It should preserve the
M1990 semantics, but use a new output directory so M1990 fail artifacts remain
unchanged:

```text
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired
```

M1995 must not run reset. If M1995 freezes an exact command, M1996 may rerun
only the reset-only validator.
