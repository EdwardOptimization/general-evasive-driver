# M2006 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Selection Quota Compatibility Implementation

- status: completed
- decision: `task_quality_calibrated_selection_quota_compatibility_implementation_pass_route_to_audit`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`
- focused tests: `6 passed`
- real measured execution in M2006: `false`
- environment rollout in M2006: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Change

M2006 implements the M2005 compatibility design:

```text
if selection_quota_name exists:
  use selection_quota_name
elif repair_axis exists:
  materialize selection_quota_name from repair_axis
else:
  fail closed with missing_repair_axis_provenance
```

The measured runner now preserves both fields in output rows:

```text
repair_axis
selection_quota_name
```

For M1986-style artifacts, this keeps the newer `repair_axis` provenance while
maintaining downstream CSV compatibility for consumers that still read
`selection_quota_name`.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_measured_runner.py
```

Result:

```text
6 passed in 0.98s
```

The new tests cover:

- M1986-style rows with `repair_axis` present and `selection_quota_name` absent;
- fallback materialization of `selection_quota_name` from `repair_axis`;
- fail-closed validation when both provenance fields are missing.

## Claim Boundary

M2006 supports:

- focused measured-runner compatibility for `selection_quota_name` /
  `repair_axis` schema generations;
- fail-closed behavior for missing repair-axis provenance;
- focused fake-rollout tests pass.

M2006 does not support:

- real measured execution completion;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next

Next milestone:

```text
m2007-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation-audit
```

M2007 should audit the focused implementation before any measured execution
rerun command design.
