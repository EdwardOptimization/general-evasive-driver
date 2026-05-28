# M1310 Paper-Route Source-History Weighted Repeat Tradeoff Audit

## Summary

M1310 ran a no-training tradeoff audit comparing:

```text
M1302 unweighted repeat
M1309 weighted repeat
M1304 failed-offset concentration
M1306 balanced split and group-weight plan
```

Decision:

```text
weighted_repeat_top_combo_partial_improvement_global_regression_route_to_robust_minfold_design
```

The M1309 weighting did partially improve the M1304 top failed
source-family/probe combo, but the global repeat result regressed. This rules
out simply increasing group weights or routing directly to PPO. The next step
should design a robust min-fold or lexicographic objective that optimizes the
worst folds and prevents lost-pass regressions.

## Command

```bash
PYTHONPATH=src python -m autodrift.source_history_weighted_repeat_tradeoff_audit \
  --weighted-run-dir runs/m1309_source_history_weighted_repeat_probe \
  --baseline-run-dir runs/m1302_source_history_trainable_scope_repeat_probe \
  --failed-offset-run-dir runs/m1304_source_history_repeat_failed_offset_audit \
  --plan-run-dir runs/m1306_source_history_concentration_refresh_plan \
  --run-dir runs/m1310_source_history_weighted_repeat_tradeoff_audit
```

## Result

```text
result_class: weighted_repeat_top_combo_partial_improvement_global_regression
baseline_repeat_offset_pass_count: 3
weighted_repeat_offset_pass_count: 1
offset_pass_count_delta: -2
new_pass_offsets: ""
lost_pass_offsets: 0|1
eval_improved_offsets: 3|4
eval_regressed_offsets: 0|1|2
best_weighted_offset: 3
best_weighted_eval_both_directional_fraction: 0.4375
best_weighted_eval_delta: 0.1517857143
mean_eval_both_directional_fraction_delta: -0.0246031746
mean_full_both_positive_count_delta: -0.8
full_improved_to_positive_count: 30
full_regressed_from_positive_count: 32
full_mean_margin_delta: -0.0151337285
group_weight_margin_delta_correlation: 0.1187303220
```

The best weighted split is genuinely better, but repeat robustness is worse.
Offsets `0` and `1` lose pass status; offset `2` regresses further; offsets `3`
and `4` improve by eval fraction, but only offset `3` is a pass.

## Offset Comparison

| Offset | Baseline pass | Weighted pass | Status | Eval delta | Full row delta | Full group delta |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 0 | true | false | lost_pass | -0.0625 | -2 | -1 |
| 1 | true | false | lost_pass | -0.1349206349 | -14 | -7 |
| 2 | false | false | regressed | -0.125 | -6 | -3 |
| 3 | true | true | improved | 0.1517857143 | 18 | 9 |
| 4 | false | false | improved | 0.0476190476 | 0 | 0 |

## Top Failed Combo

M1304's top failed combo was:

```text
source_family_pair: single_wheel_grip_collapse->single_wheel_grip_collapse
probe_template: left_brake_probe
```

M1310 finds:

```text
top_failed_combo_group_count: 105
top_failed_combo_baseline_positive_count: 12
top_failed_combo_weighted_positive_count: 15
top_failed_combo_positive_delta: +3
top_failed_combo_improved_to_positive_count: 14
top_failed_combo_regressed_from_positive_count: 11
top_failed_combo_mean_margin_delta: -0.0137132418
top_failed_combo_mean_group_weight: 1.3254313320
```

This is partial improvement, not robust repair. More groups flip positive than
negative inside the top combo, but the average margin still decreases and the
global pass count drops.

## Weight-Gain Relationship

```text
improved_to_positive_count: 30, mean_group_weight: 1.2962914654
regressed_from_positive_count: 32, mean_group_weight: 1.2574029503
margin_improved_count: 111, mean_group_weight: 1.2484520545
margin_regressed_count: 207, mean_group_weight: 1.2455847278
group_weight_margin_delta_correlation: 0.1187303220
```

Weights are not a clean control variable. Higher weights slightly correlate
with margin gains, but regressions are frequent and not isolated to low-weight
groups. The problem is a global fold/objective tradeoff rather than a missing
scalar coefficient.

## Interpretation

Supported:

```text
M1309 weighting targeted the intended concentrated failure family enough to
produce partial top-combo improvement.
```

Supported:

```text
The improvement is not robust across folds. It creates lost-pass regressions in
offsets 0 and 1 and worsens offset 2.
```

Falsified:

```text
The M1306 weighted plan improves repeat robustness over M1302.
```

Falsified:

```text
The next step should be more scalar weight pressure or PPO.
```

Not tested:

```text
Closed-loop public replay retention, private holdout generalization, real
vehicle transfer, high-fidelity simulation, or level3 anticipatory
self-identification.
```

## Failure Taxonomy

Primary:

```text
objective_overfit
```

Reason:

```text
The weighted objective creates a strong local best split and partial top-combo
repair while degrading repeat pass count.
```

Secondary:

```text
scenario_sampling_failure risk
```

Reason:

```text
The fixed source-history corpus and fold plan still leave a fold-level tradeoff
that simple group weighting cannot resolve.
```

Not observed:

```text
contract_violation
training_instability
private_holdout_contamination
promotion_gate_failure
```

## Next Step

M1311 should design a robust min-fold or lexicographic source-history objective.

Required design properties:

- Treat repeat folds as first-class constraints, not averaged diagnostics.
- Prevent lost-pass regressions on baseline passing folds.
- Improve failed folds only after protecting already passing folds.
- Preserve group-level no pair-specific-weight discipline.
- Keep PPO and promotion blocked until the objective passes repeat robustness.

The expected next route is a design milestone, not another training run.
