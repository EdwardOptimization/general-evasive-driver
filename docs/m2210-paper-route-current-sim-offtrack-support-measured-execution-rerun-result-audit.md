# M2210 Paper-Route Current-Sim Offtrack-Support Measured-Execution Rerun Result Audit

- status: completed
- decision: `current_sim_offtrack_support_measured_execution_audit_not_comparison_ready_route_to_outcome_localization_design`
- manifest: `experiments/manifests/m2210-paper-route-current-sim-offtrack-support-measured-execution-rerun-result-audit.json`
- audited summary: `runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json`
- audited episode rows: `runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv`
- follow-up manifest: `experiments/manifests/m2211-paper-route-current-sim-offtrack-support-outcome-localization-design.json`
- measured execution in M2210: `false`
- policy action executed in M2210: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Execution Completeness

M2209 execution is complete:

```text
result_class: current_sim_controlled_comparison_measured_execution_pass
episode_count: 2304
failure_count: 0
spec_count: 288
profile_count: 8
metadata_missing_count: 0
metric_completeness_failure_count: 0
task_family_quota_pass: true
profile_quota_pass: true
history_representation_quota_pass: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
environment_rollout_started: true
policy_action_executed: true
```

The M2204 metadata blocker is repaired.

## Outcome Support

Raw outcome distribution:

```text
success_obstacle_pass: 374 / 2304 = 0.1623263888888889
collision_failure: 49 / 2304 = 0.021267361111111112
off_track_noncollision_noncompletion: 1881 / 2304 = 0.81640625
```

This is still offtrack dominated.

Task family success rates are descriptive only:

```text
T1_reactive_emergency_avoidance: 0.328125
T2_delayed_actuator_response: 0.25833333333333336
T3_diagnostic_warmup_obstacle_reveal: 0.19886363636363635
T4_same_current_different_older_history: 0.15892857142857142
T5_terminal_boundary_near_constraint: 0.07015306122448979
```

Profile aggregates are also descriptive only and must not be treated as a
ranking before denominator-backed support checks.

## Classification

Failure type:

```text
scenario_sampling_failure
```

M2209 provides clean closed-loop data, but the data is not comparison-ready.
The panel still has too much offtrack noncompletion to support a fair
controller-family comparison or paper-level result.

## Decision

Comparison-ready:

```text
false
```

Reason:

```text
off_track_noncollision_noncompletion rate = 0.81640625
success_obstacle_pass rate = 0.1623263888888889
```

The result is useful because it proves the repaired workload can run end to
end. It does not yet prove that the task panel has enough balanced outcome
support for L0/L1/L2/L3 comparison.

## Next Step

M2211 should design a no-rerun outcome localization audit over M2209 artifacts.
That audit should identify:

```text
which task families, source templates, capability pairs, and profile groups
are driving offtrack dominance;
whether any slices are comparison-ready or near comparison-ready;
whether repair should target scenario sampling, task geometry, profile training,
or a narrower denominator-backed comparison slice.
```

M2211 must not rerun measured execution or rank profiles.
