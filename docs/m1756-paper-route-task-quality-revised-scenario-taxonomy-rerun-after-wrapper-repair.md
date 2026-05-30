# M1756 Paper-Route Task-Quality Revised Scenario Taxonomy Rerun After Wrapper Repair

- status: completed
- result class: `task_quality_scenario_taxonomy_execution_incomplete_or_fail`
- execution passed: `false`
- wrapper repair verified: `true`
- output dir: `runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair`
- training/replay/PPO: false

## Summary

M1756 reran the fixed revised public diagnostic protocol after the M1755 wrapper
config proxy repair. The dominant M1753 wrapper failure is gone:

```text
AttributeError count: 0
```

The execution still does not pass because one reset-time sampling failure
remains. The result is therefore a successful wrapper-repair verification plus a
single-sampling-failure blocker, not a controller-family or paper-level result.

## Counts

```text
result_class: task_quality_scenario_taxonomy_execution_incomplete_or_fail
episode_count: 863
target_episode_count: 864
failure_count: 1
profile_count: 12
scenario_spec_count: 72
scenario_family_count: 6
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

## Remaining Failure

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
scenario_family: unavoidable_mitigation
evaluation_role: mitigation_diagnostic
primary_metric_family: collision_mitigation
hidden_dynamics_bucket: low_mu
error_type: RuntimeError
error_message: failed to sample an obstacle scenario matching the configured filters
```

This is the same secondary failure observed in M1753.

## Completed Rows Snapshot

Completed rows:

```text
success_obstacle_pass: 73
collision_failure: 279
off_track_noncollision_noncompletion: 511
```

The matrix is almost complete but not complete enough for controller-family
ranking or paper-level interpretation. The missing row is in a
mitigation-diagnostic family and must be audited before any repair or rerun.

## Guardrails

- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- unsupported faults treated as covered: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- wrapper repair removed the M1753 `AttributeError` failure mode;
- revised execution now reaches `863/864` rows with clean metric completeness on
  completed rows;
- one deterministic reset-time sampling failure remains.

Unsupported:

- revised execution pass;
- controller-family ranking;
- profile comparison;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Decision

Route to M1757 single sampling-failure audit before changing seeds/specs or
interpreting partial completed rows.
