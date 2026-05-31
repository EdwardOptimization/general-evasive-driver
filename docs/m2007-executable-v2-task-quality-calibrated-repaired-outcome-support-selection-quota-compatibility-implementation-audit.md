# M2007 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Selection Quota Compatibility Implementation Audit

- status: completed
- decision: `task_quality_calibrated_selection_quota_compatibility_audit_admit_measured_execution_rerun_command_design`
- audited implementation: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- audited tests: `tests/test_executable_v2_task_quality_calibrated_measured_runner.py`
- real measured execution in M2007: `false`
- environment rollout in M2007: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2006 is a clean focused compatibility repair.

The measured runner now:

```text
1. preserves repair_axis in output rows;
2. materializes selection_quota_name from repair_axis when the legacy field is missing;
3. fails closed with missing_repair_axis_provenance when both fields are missing.
```

Focused tests passed:

```text
6 passed
```

This repairs the M2003 zero-row validation blocker without mutating M1986
artifacts in place and without changing actor inputs, rewards, dynamics,
profile configs, or controller policies.

## Supported Claims

M2007 supports:

- selection quota compatibility is implemented and test-covered;
- M1986-style rows with `repair_axis` and no `selection_quota_name` can pass
  focused measured-runner validation;
- rows missing both provenance fields still fail closed;
- measured execution rerun command design is now admitted.

M2007 does not support:

- real measured execution completion;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next Route

Decision:

```text
admit_measured_execution_rerun_command_design
```

Next milestone:

```text
m2008-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-v2-command-design
```

M2008 should freeze a fresh measured execution rerun command. It must not run
the measured execution.
