# M1295 Paper-Route Source-History Pair-Group Objective Probe

## Summary

M1295 implements and runs the bounded no-PPO actor_mean-only pair-group
directional objective probe designed in M1294.

Decision:

```text
source_history_pair_group_objective_mixed_route_to_result_audit
```

Result class:

```text
source_history_pair_group_objective_mixed
```

The pair-group objective gives a small improvement over M1292, but not enough to
claim directional repair.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_pair_group_objective_probe.py
```

Result:

```text
1 passed in 1.64s
```

Probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_pair_group_objective_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --m1288-checkpoint runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1295_source_history_pair_group_objective_probe \
  --device cpu \
  --steps 500 \
  --lr 0.0003 \
  --target-margin 0.05
```

## Implementation

Added:

```text
src/autodrift/source_history_pair_group_objective_probe.py
tests/test_source_history_pair_group_objective_probe.py
```

The probe:

```text
groups rows by pair_id/probe_template;
optimizes actor_mean only;
adds group floor and group balance terms;
reports row-level and group-level metrics;
writes diagnostic candidates only;
does not run PPO or promote.
```

## Result

Best candidate:

```text
best_init_name: base_init
best_candidate_class: pair_group_directional_mixed
best_both_directional_fraction: 0.1973684211
best_both_positive_count: 30
best_mutually_exclusive_fraction: 0.6710526316
best_group_all_rows_both_positive_count: 15
best_group_all_rows_both_positive_fraction: 0.1973684211
best_group_any_row_both_positive_count: 15
best_group_min_margin_mean: -0.2857604090
best_group_min_margin_p10: -1.8031842709
```

M1292 baseline for comparison:

```text
best_both_directional_fraction: 0.1842105263
best_both_positive_count: 28
best_group_all_rows_both_positive_count: 14
```

M1295 improvement:

```text
both-positive rows: +2
all-rows-both-positive groups: +1
mutually_exclusive_fraction: 0.7763157895 -> 0.6710526316
```

This is a real but small directional improvement.

## Gate Outcome

Strong M1294 gate required:

```text
group_all_rows_both_positive_fraction >= 0.25
both_directional_fraction >= 0.25
group_all_rows_both_positive_count > 14
non_actor_mean_mutation_detected == false
```

M1295 outcome:

```text
group_all_rows_both_positive_fraction: 0.1973684211
both_directional_fraction: 0.1973684211
group_all_rows_both_positive_count: 15
any_non_actor_mean_mutation_detected: false
```

Therefore:

```text
mixed, not strong.
```

## Guardrails

M1295 preserved:

```text
any_non_actor_mean_mutation_detected: false
labels_enter_actor_input: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
```

## Interpretation

Supported:

```text
Pair-group objective improves the source-history directional relation slightly
more than M1292.
```

Not supported:

```text
Pair-group actor_mean-only objective solves directional repair.
```

Not supported:

```text
PPO readiness or checkpoint promotion.
```

## Next Step

Pre-register:

```text
m1296-paper-route-source-history-pair-group-objective-result-audit
```

M1296 is the tenth milestone in the
`paper_route_source_history_objective_only_update` branch. It should audit M1295
and then route to branch synthesis before more narrow implementation work.

Likely branch-level conclusion:

```text
actor_mean-only objectives are connected and can produce small directional
improvements, but they are not sufficient to repair the source-history gate.
The next branch should decide between trainable-scope escalation and
source-history corpus refresh.
```

PPO and promotion remain blocked.
