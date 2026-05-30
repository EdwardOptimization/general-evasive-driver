# M1753 Paper-Route Task-Quality Revised Scenario Taxonomy Measured Execution

- status: completed
- result class: `task_quality_scenario_taxonomy_execution_incomplete_or_fail`
- execution passed: `false`
- output dir: `runs/m1753_revised_scenario_taxonomy_execution`
- training/replay/PPO: false

## Summary

M1753 executed the pre-registered revised public diagnostic command from M1752.
The execution did not pass: it completed `504/864` episode rows and wrote `360`
failure rows.

This is an execution-plumbing failure, not a controller-family or
self-identification result. The completed rows cannot be used for ranking or
paper-level interpretation.

## Counts

```text
result_class: task_quality_scenario_taxonomy_execution_incomplete_or_fail
episode_count: 504
target_episode_count: 864
failure_count: 360
profile_count: 7
target_profile_count: 12
scenario_spec_count: 72
scenario_family_count: 6
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

## Failure Breakdown

Dominant failure:

```text
359 x AttributeError:
'ControllerProfileObservationWrapper' object has no attribute 'config'
```

Affected profiles:

```text
L0_current_masked
L2_window_13_current_tiled
L2_window_25_current_tiled
L2_window_50_current_tiled
L2_window_100_current_tiled
```

The likely cause is that masked/current-tiled profile wrappers do not proxy
`env.config`, while the evaluator now needs `env.config` to compute logging-only
outcome metrics.

Secondary failure:

```text
1 x RuntimeError:
failed to sample an obstacle scenario matching the configured filters
```

The reset-time sampling failure occurs at:

```text
workload_id: m1728-s4-02::L2_window_13_current_tiled
scenario_family: unavoidable_mitigation
primary_metric_family: collision_mitigation
hidden_dynamics_bucket: low_mu
```

## Completed Rows Snapshot

Completed episode rows are balanced across the six scenario families:

```text
84 rows per scenario family
```

Outcome snapshot from completed rows:

```text
success_obstacle_pass: 59
collision_failure: 160
off_track_noncollision_noncompletion: 285
```

These counts are diagnostic only and are not interpretable as controller-family
ranking because five profile families failed systematically.

## Guardrails

- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- unsupported faults treated as covered: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1753 ran the pre-registered command and produced failure evidence;
- metric completeness on completed rows passed;
- dominant failure is a wrapper/evaluator plumbing issue;
- one reset-time sampling failure remains after the wrapper issue is accounted
  for.

Unsupported:

- revised execution pass;
- controller-family ranking;
- profile comparison;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Decision

Route to M1754 execution-failure audit. The audit should decide whether to
repair the wrapper `config` proxy first, separately inspect the single sampling
failure, or redesign the execution protocol.
