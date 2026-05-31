# M2005 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Selection Quota Compatibility Design

- status: completed
- decision: `task_quality_calibrated_selection_quota_compatibility_design_admit_focused_implementation`
- code edited in M2005: `false`
- measured execution in M2005: `false`
- environment rollout in M2005: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M2003 failed closed before rollout because the measured runner still required
the legacy field:

```text
selection_quota_name
```

M1986 repaired outcome-support artifacts do not contain that field. They do
contain complete newer repair provenance:

```text
repair_axis
repair_source_kind
source_role_semantics
normalized_surface_variant
```

Therefore the repair should not mutate M1986 artifacts in place and should not
silently drop provenance requirements. The measured runner should accept
`repair_axis` as the newer provenance field when `selection_quota_name` is
absent.

## Design

M2006 should implement runner-side compatibility in
`src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`.

### Provenance Rule

For both executable specs and workload rows:

```text
if selection_quota_name is non-empty:
  use selection_quota_name
elif repair_axis is non-empty:
  use repair_axis as selection_quota_name fallback
else:
  fail closed
```

This is not a semantic relaxation. It keeps one required repair-axis provenance
field while supporting the two schema generations:

```text
legacy calibrated materialization: selection_quota_name
repaired outcome-support materialization: repair_axis
```

### Output Compatibility

`CALIBRATED_PASSTHROUGH_FIELDS` should include:

```text
repair_axis
selection_quota_name
```

Episode and failure rows should materialize:

```text
repair_axis: original repair_axis when available
selection_quota_name: original selection_quota_name, otherwise repair_axis
```

This preserves downstream CSV compatibility for consumers that still expect
`selection_quota_name`, while retaining the newer explicit `repair_axis` field.

### Validation

The required field check should no longer require raw `selection_quota_name` to
be present. Instead it should require repair-axis provenance:

```text
selection_quota_name or repair_axis
```

If both are missing, validation must fail closed with a clear error type such
as:

```text
missing_repair_axis_provenance
```

The existing quota metadata requirements remain unchanged:

```text
repair_source_kind
source_role_semantics
normalized_surface_variant
```

### Summary Fields

M2006 may add summary fields for auditability:

```text
selection_quota_name_fallback_count
selection_quota_name_missing_count
repair_axis_missing_count
```

These are not pass gates by themselves. The pass gate is that validation does
not accept rows missing both provenance fields.

## Focused Tests

M2006 should add focused fake-rollout tests for:

```text
1. M1986-style rows:
   repair_axis present, selection_quota_name absent.
   The fake measured execution passes validation, emits episode rows, and fills
   selection_quota_name from repair_axis.

2. Legacy rows:
   selection_quota_name present.
   Existing behavior remains valid.

3. Missing both:
   selection_quota_name absent and repair_axis absent.
   Validation fails closed before rollout with missing_repair_axis_provenance.

4. Artifact schema:
   episode/failure rows include both repair_axis and selection_quota_name.
```

M2006 must not run the real 960-row measured execution. A later command design
or rerun milestone must handle the actual M2003 rerun.

## Claim Boundary

M2005 supports only:

```text
a bounded measured-runner schema compatibility design.
```

M2005 does not support:

- measured execution completion;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next

Next milestone:

```text
m2006-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-implementation
```

M2006 should implement the focused compatibility repair and tests only.
