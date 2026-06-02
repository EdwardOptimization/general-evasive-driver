# M2443 Paper-Route Current-Sim Dual-Axis Metric-Selected Validation Preflight Implementation

- status: completed
- result_class: `current_sim_dual_axis_metric_selected_validation_preflight_pass`
- manifest: `experiments/manifests/m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_metric_selected_validation_preflight.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_metric_selected_validation_preflight.py`
- summary: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/summary.json`
- workload rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/workload_rows.csv`
- reset validation rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/reset_validation_rows.csv`
- decision rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/decision_rows.csv`
- new measured rollout/policy action/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result

M2443 materialized the M2413 denominator under the metric-selected soft-boundary
config and ran reset/config/shape preflight only.

```text
workload_row_count: 5250
reset_target_count: 350
selected_checkpoint_count: 15
source_m2413_episode_count: 5250
source_m2413_reset_target_count: 350
source_m2413_selected_checkpoint_count: 15
source_m2413_unique_cell_count: 5250
source_m2413_duplicate_cell_count: 0
missing_source_target_count: 0
missing_source_selected_checkpoint_count: 0
missing_source_cell_count: 0
environment_reset_success_count: 350
actor_observation_shape_changed_count: 0
finite_observation_count: 350
soft_enabled_reset_count: 350
policy_action_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Primary soft-boundary config:

```text
soft_offtrack_metric_enabled: true
soft_offtrack_tolerance_m: 0.20
sensitivity_thresholds_m: 0.02, 0.05, 0.10, 0.20
```

## Implementation Notes

The preflight writes a metric-selected workload cross product for the M2413
source-linked reset targets and selected checkpoints. It also validates source
coverage at cell level, not only by total row count:

```text
350 reset targets x 15 selected checkpoints = 5250 cells
unique source cells: 5250
duplicate source cells: 0
missing source cells: 0
```

For each reset target, M2443 builds the original env config and the
soft-boundary env config, compares actor observation shape, resets the
soft-boundary env, and stops immediately. It does not call a policy, execute an
environment step, run repair, train, replay, use PPO, rank candidates, rank
controllers, select a winner, or claim a driving result.

## Focused Tests

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_dual_axis_metric_selected_validation_preflight.py
```

Result:

```text
4 passed
```

Covered:

```text
metric-selected workload materializes and reset-preflights successfully;
soft-boundary config preserves actor-contract fields and track width;
source target gaps fail closed as scenario_sampling_failure;
source cell gaps and duplicates fail closed as scenario_sampling_failure.
```

## Contract Boundary

Allowed claim:

```text
The M2413 denominator can be materialized and reset-tested under the
metric-selected soft-boundary env config without changing actor observation
shape or executing policy actions.
```

Blocked claims:

```text
actual success improvement
measured driving performance
scenario redesign execution
candidate-family ranking
controller-family ranking
current-sim verdict
paper-level result
finite-window vs GRU conclusion
level3 self-identification evidence
training repair success
```

## Next Step

Next milestone:

```text
m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit
```

M2444 should audit the M2443 preflight and decide whether it admits the bounded
full metric-selected measured-validation route. It must not run rollout,
repair, training, ranking, winner selection, or verdict claims.
