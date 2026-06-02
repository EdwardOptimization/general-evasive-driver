# M2445 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Implementation

- status: completed
- result_class: `current_sim_dual_axis_metric_selected_measured_validation_pass`
- manifest: `experiments/manifests/m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_metric_selected_measured_validation.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_metric_selected_measured_validation.py`
- summary: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/summary.json`
- episode rows: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/episode_rows.csv`
- aggregate rows: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/aggregate_rows.csv`
- decision rows: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/decision_rows.csv`
- measured rollout/policy action: `true`
- repair/training/replay/PPO: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result

M2445 executed the audited M2443 workload under the metric-selected
soft-boundary env config.

```text
episode_count: 5250
target_episode_count: 5250
source_reset_target_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
```

Primary measured metrics:

```text
metric_selected_actual_success_count: 351
metric_selected_actual_success_rate: 0.06685714285714285
metric_selected_hard_offtrack_failure_count: 3921
metric_selected_hard_offtrack_failure_rate: 0.7468571428571429
metric_selected_soft_offtrack_violation_count: 17
metric_selected_soft_offtrack_violation_rate: 0.0032380952380952383
metric_selected_boundary_tolerated_success_count: 0
metric_selected_boundary_tolerated_success_rate: 0.0
metric_selected_max_offtrack_overshoot_mean: 0.20611995305532116
metric_selected_max_offtrack_overshoot_max: 0.4325018735577544
```

Global aggregate row:

```text
success_rate: 0.06685714285714285
collision_rate: 0.1761904761904762
offtrack_rate: 0.7453333333333333
max_step_noncompletion_rate: 0.006285714285714286
other_failure_rate: 0.005333333333333333
dominant_failure_mode: offtrack_dominated_failure
diagnostic_only: true
ranking_admissible: false
winner_selected: false
```

These are measured artifact values, not a current-sim verdict.

## Implementation Notes

M2445 uses the M2443 workload/preflight artifacts as the execution denominator.
It constructs metric-selected reset specs by overlaying:

```text
soft_offtrack_metric_enabled: true
soft_offtrack_tolerance_m: 0.20
```

The runner preserves original and metric-selected reset target keys:

```text
original_reset_target_key
metric_selected_reset_target_key
original_env_config_hash
metric_selected_env_config_hash
```

It also writes row-level task-boundary fields:

```text
metric_selected_actual_success
metric_selected_hard_offtrack_failure
metric_selected_soft_offtrack_violation
metric_selected_boundary_tolerated_success
metric_selected_max_offtrack_overshoot_m
```

## Focused Tests

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_dual_axis_metric_selected_measured_validation.py
```

Result:

```text
2 passed
```

Covered:

```text
injected rollout path writes complete episode and decision artifacts;
metric-selected soft/hard boundary fields are summarized;
validation gaps fail closed before rollout.
```

## Contract Boundary

Allowed claim:

```text
The audited 350 x 15 M2443 workload was executed under metric-selected
soft-boundary task metrics and produced complete measured rows with zero
failure, validation, metadata, metric-completeness, actor-contract, or guardrail
failures.
```

Blocked claims:

```text
actual success improvement
candidate-family ranking
controller-family ranking
winner selection
scenario redesign execution
repair execution
training repair success
paper-level result
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next Step

Next milestone:

```text
m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit
```

M2446 should audit M2445 before any interpretation. In particular, it should
explain the measured mismatch between high old-row diagnostic soft success and
the fresh soft-boundary execution, while preserving that M2445 itself does not
make a verdict or ranking claim.
