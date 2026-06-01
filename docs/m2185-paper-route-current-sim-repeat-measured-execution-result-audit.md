# M2185 Paper-Route Current-Sim Repeat Measured Execution Result Audit

- status: completed
- decision: `current_sim_repeat_measured_execution_audit_route_to_seed_diversity_and_combined_outcome_audit_design`
- manifest: `experiments/manifests/m2185-paper-route-current-sim-repeat-measured-execution-result-audit.json`
- audited summary: `runs/m2184_paper_route_current_sim_repeat_measured_execution/summary.json`
- training in M2185: `false`
- additional measured execution in M2185: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2184 is accepted as complete execution and metadata-clean repeat data:

```text
result_class: current_sim_controlled_comparison_measured_execution_pass
episode_count: 640
failure_count: 0
spec_count: 40
profile_count: 8
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
task_family_quota_pass: true
profile_quota_pass: true
history_representation_quota_pass: true
```

Repeat metadata is present:

```text
training_repeat_aggregate.csv exists
repeat_1_seed_21761: 320 episodes, success_rate 0.15625, collision_rate 0.05625
repeat_2_seed_21762: 320 episodes, success_rate 0.15625, collision_rate 0.05625
```

## Why It Is Not Comparison-Ready Yet

Raw M2184 outcomes:

```text
success_obstacle_pass: 100 / 640 = 0.15625
collision_failure: 36 / 640 = 0.05625
off_track_noncollision_noncompletion: 504 / 640 = 0.78750
```

Raw M2174 one-seed outcomes for context:

```text
success_obstacle_pass: 63 / 320 = 0.196875
collision_failure: 20 / 320 = 0.06250
off_track_noncollision_noncompletion: 237 / 320 = 0.740625
```

This is useful closed-loop data, but still low-support and offtrack-dominated.
The profile aggregate in M2184 must remain descriptive and cannot be used as a
winner table.

The two new repeat groups also have identical repeat-level aggregate values.
That may be benign, but it must be audited before the project treats the repeat
panel as seed-diverse evidence.

## Decision

Do not rank profiles from M2184.

Do not make a finite-window vs GRU verdict.

Do not claim paper-level benchmark evidence.

Route to a no-rerun audit design that checks:

```text
combined M2174 + M2184 outcome support;
repeat seed/profile diversity;
whether repeat_1 and repeat_2 are genuinely independent enough for comparison;
whether the current panel needs task-quality/offtrack repair before ranking.
```

## Next Step

M2186 should design a no-rerun seed-diversity and combined-outcome audit. It
should not execute new rollouts or rank profiles.
