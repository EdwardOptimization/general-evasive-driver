# M2004 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Execution Rerun Result Audit

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_audit_route_to_selection_quota_compatibility_design`
- audited summary: `runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/summary.json`
- measured execution in M2004: `false`
- environment rollout in M2004: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2003 is a clean fail-closed validation result, not a driver-performance result:

```text
result_class: task_quality_calibrated_measured_execution_incomplete_or_fail
episode_count: 0
failure_count: 0
environment_rollout_started: false
measured_rollout_started: false
policy_action_executed: false
guardrail_violation_count: 0
```

The M2000 quota repair is not the blocker:

```text
expected_quota_source: workload
quota_metadata_missing_count: 0
expected_source_kind_counts:
  anchor_neighborhood: 288
  mitigation_isolation_check: 240
  offtrack_boundary_relief: 192
  success_stabilizer: 240
```

The immediate blocker is a schema compatibility field:

```text
validation_failure_rows: 1040
missing_spec_field selection_quota_name: 80
missing_workload_field selection_quota_name: 960
```

## Diagnosis

`selection_quota_name` is an older calibrated materialization field used by the
measured runner as a required passthrough field. The M1986 repaired
outcome-support artifacts instead carry:

```text
repair_axis
repair_source_kind
source_role_semantics
normalized_surface_variant
```

The M1986 workload has complete `repair_axis` provenance:

```text
offtrack_anchor_relief: 288
success_support_expansion: 240
offtrack_boundary_relief_extension: 192
collision_mitigation_relief: 144
mitigation_metric_isolation: 96
```

The M1986 executable specs have the corresponding `80` source-level
`repair_axis` rows. Therefore this is a local measured-runner schema
compatibility issue: the runner should not require the legacy
`selection_quota_name` field when the newer `repair_axis` field is present.

## Supported Claims

M2004 supports:

- M2003 did not reach rollout;
- M2003 should not be interpreted as policy/controller performance;
- workload-derived quota computation worked far enough to report expected
  M1986 quota counts;
- the next blocker is legacy `selection_quota_name` compatibility.

M2004 does not support:

- measured execution completion;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- policy improvement;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_selection_quota_compatibility_design
```

Next milestone:

```text
m2005-executable-v2-task-quality-calibrated-repaired-outcome-support-selection-quota-compatibility-design
```

M2005 should design a no-rollout measured-runner compatibility repair:

```text
if selection_quota_name is missing and repair_axis is present:
  treat repair_axis as the repair-axis provenance field
  optionally materialize selection_quota_name from repair_axis for downstream CSV compatibility

if both selection_quota_name and repair_axis are missing:
  fail closed
```

M2005 must not edit code, rerun measured execution, rank controller families, or
make paper-level claims.
