# M2003 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Execution Rerun

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_validation_fail_route_to_audit`
- summary: `runs/m2003_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun/summary.json`
- measured execution command used: frozen M2002 command
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2003 ran the frozen M2002 command and failed closed before rollout:

```text
result_class: task_quality_calibrated_measured_execution_incomplete_or_fail
episode_count: 0
target_episode_count: 960
failure_count: 0
spec_count: 0
profile_count: 0
environment_rollout_started: false
measured_rollout_started: false
policy_action_executed: false
guardrail_violation_count: 0
```

The repaired workload-derived quota path did work:

```text
expected_quota_source: workload
quota_metadata_missing_count: 0
expected_source_kind_counts:
  anchor_neighborhood: 288
  mitigation_isolation_check: 240
  offtrack_boundary_relief: 192
  success_stabilizer: 240
```

The quota gates failed only because there were no episode rows after validation
stopped execution:

```text
source_kind_counts: {}
source_kind_quota_pass: false
role_surface_counts: {}
role_surface_quota_pass: false
```

## Validation Failure

The immediate validation failure is missing `selection_quota_name`:

```text
validation_failure_rows: 1040
missing_spec_field selection_quota_name: 80
missing_workload_field selection_quota_name: 960
```

This is a schema/readiness issue, not a policy outcome. The M1986 repaired
outcome-support artifacts use `repair_axis` and related repair metadata, but do
not contain the older calibrated runner field `selection_quota_name`.

## Supported Claims

M2003 supports:

- the frozen M2002 command was executed;
- the repaired measured runner computes expected quotas from the active
  workload;
- the M1986 artifacts still fail measured-runner validation before rollout
  because `selection_quota_name` is missing;
- no rollout, training, replay, PPO, controller ranking, or paper-level claim
  happened.

M2003 does not support:

- measured execution completion;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU comparison;
- level3 self-identification.

## Next

Next milestone:

```text
m2004-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-execution-rerun-result-audit
```

M2004 must audit the validation failure before any repair, rerun, ranking, or
interpretation.
