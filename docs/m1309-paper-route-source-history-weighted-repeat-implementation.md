# M1309 Paper-Route Source-History Weighted Repeat Implementation

## Summary

M1309 implemented and ran the bounded weighted source-history repeat required by
M1307/M1308.

Decision:

```text
source_history_weighted_repeat_mixed_regression_route_to_tradeoff_audit
```

The implementation is valid infrastructure: it uses the M1306 balanced split
plan, uses capped group weights, reports weighted diagnostics, avoids
pair-specific weights, and does not mutate forbidden parameter groups.

Scientifically, the weighted repeat is not an improvement over M1302. The best
single split improves strongly, but repeat robustness regresses from `3/5`
offset passes to `1/5`. This keeps PPO, promotion, private holdout use, and
closed-loop self-identification claims blocked.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q tests/test_source_history_trainable_scope_probe.py
```

Weighted repeat:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_trainable_scope_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1309_source_history_weighted_repeat_probe \
  --device cpu \
  --steps 400 \
  --lr 0.0002 \
  --target-margin 0.05 \
  --scopes fusion_head \
  --split-plan runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv \
  --group-weight-rows runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv \
  --split-offsets 0,1,2,3,4
```

## Implementation

M1309 extends `source_history_trainable_scope_probe` with:

- `--split-plan` loading from M1306 `balanced_split_rows.csv`.
- Pair-disjoint split-plan validation.
- `--group-weight-rows` loading from M1306 `group_weight_rows.csv`.
- Row-level weighted correct/wrong source-history losses.
- Weighted pair-group floor and balance losses.
- Weighted diagnostic output at
  `runs/m1309_source_history_weighted_repeat_probe/weighted_group_diagnostics.csv`.
- Summary fields for split/weight use, pair-specific weight detection, maximum
  group weight, and weighted loss enablement.

The focused test now covers the split-plan and group-weight path.

## Result

Overall:

```text
result_class: source_history_trainable_scope_repeat_mixed
split_plan_used: true
group_weights_used: true
weighted_loss_enabled: true
pair_specific_weight_used: false
max_group_weight: 2.0
forbidden_parameter_mutation_detected: false
best_split_offset: 3
best_eval_both_directional_fraction: 0.4375
best_eval_group_all_rows_both_positive_fraction: 0.4375
best_full_both_positive_count: 58
best_full_group_all_rows_both_positive_count: 29
best_repeat_offset_pass_count: 1
best_repeat_required_pass_count: 3
best_repeat_mean_eval_both_directional_fraction: 0.2089285714
best_repeat_mean_eval_group_all_rows_both_positive_fraction: 0.2089285714
best_repeat_mean_full_both_positive_count: 37.2
best_repeat_mean_full_group_all_rows_both_positive_count: 18.6
```

Per-offset summary:

| Offset | Eval row/group fraction | Full rows | Full groups | Class |
| --- | ---: | ---: | ---: | --- |
| 0 | 0.1875 | 44 | 22 | mixed |
| 1 | 0.1428571429 | 34 | 17 | mixed |
| 2 | 0.0625 | 26 | 13 | negative |
| 3 | 0.4375 | 58 | 29 | strong |
| 4 | 0.2142857143 | 24 | 12 | negative |

## Comparison To M1302

M1302 unweighted repeat:

```text
offset_pass_count: 3/5
mean_eval_both_directional_fraction: 0.2335317460
mean_eval_group_all_rows_both_positive_fraction: 0.2335317460
mean_full_both_positive_count: 38.0
mean_full_group_all_rows_both_positive_count: 19.0
best_eval_fraction: 0.2857142857
best_full_both_positive_count: 40
best_full_group_all_rows_both_positive_count: 20
```

M1309 weighted repeat:

```text
offset_pass_count: 1/5
mean_eval_both_directional_fraction: 0.2089285714
mean_eval_group_all_rows_both_positive_fraction: 0.2089285714
mean_full_both_positive_count: 37.2
mean_full_group_all_rows_both_positive_count: 18.6
best_eval_fraction: 0.4375
best_full_both_positive_count: 58
best_full_group_all_rows_both_positive_count: 29
```

The weighted repeat improved the best offset but reduced repeat robustness and
slightly reduced mean full counts. This is compatible with a weight-induced
tradeoff or fold-specific overfit, not a robust improvement.

## Supported Claims

Supported:

```text
The weighted repeat path is implemented and test-covered.
```

Supported:

```text
M1306 split and weight artifacts can be used without pair-specific weights or
forbidden parameter mutation.
```

Supported:

```text
Offset 3 benefits strongly from the weighted setup.
```

## Not Supported

Not supported:

```text
The M1306 weighted plan improves repeat robustness over M1302.
```

Not supported:

```text
Weighted fixed-current diagnostics justify PPO continuation or checkpoint
promotion.
```

Not supported:

```text
This result proves closed-loop self-identification.
```

## Failure Taxonomy

Primary classification:

```text
objective_overfit
```

Reason:

```text
The weighted objective improves one split strongly while degrading repeat
robustness across the other splits.
```

Secondary classification:

```text
scenario_sampling_failure risk
```

Reason:

```text
The fold/corpus weighting may still be underspecified for concentrated
source-family/probe-template failures.
```

Not observed:

```text
contract_violation
forbidden_parameter_mutation
private_holdout_contamination
promotion_gate_failure
training_instability
```

## Next Step

M1310 should run a no-training tradeoff audit:

```text
M1302 baseline repeat
vs
M1309 weighted repeat
vs
M1304 failed-offset concentration
vs
M1306 split/weight plan
```

The audit should determine whether M1309 is:

- single-fold overfit,
- weight-induced tradeoff,
- top failed-combo improvement with global regression,
- or evidence that the current source-history corpus/plan is insufficient.

Until that audit is complete, PPO and promotion remain blocked.
