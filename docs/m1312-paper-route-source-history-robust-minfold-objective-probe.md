# M1312 Paper-Route Source-History Robust Min-Fold Objective Probe

## Summary

M1312 implemented and ran the bounded no-PPO robust min-fold source-history
repeat probe designed in M1311.

Decision:

```text
robust_minfold_repeat_mean_positive_lost_pass_tradeoff_route_to_result_audit
```

The robust min-fold objective improves the global repeat mean and the top failed
combo relative to M1302 and M1309, but it fails the M1311 lexicographic
non-regression rule because it loses baseline passing offsets `0|1`.

PPO and promotion remain blocked.

## Implementation

M1312 extends `source_history_trainable_scope_probe` with:

- `--baseline-repeat-run-dir`
- `--robust-minfold`
- `--bucket-columns`
- `--lambda-bucket-cvar`
- `--lambda-retention`
- `--retention-margin-eps`
- `--minfold-temperature`

The robust objective adds:

```text
bucket/CVaR loss over source-family/probe/margin-bucket groups
passing-fold retention loss from M1302 baseline full-group rows
```

The implementation keeps:

```text
P0 actor input contract unchanged
pair-disjoint split plan
group-level weights only
no pair-specific weights
no PPO
no private holdout
no promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_trainable_scope_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1312_source_history_robust_minfold_probe \
  --device cpu \
  --steps 400 \
  --lr 0.0002 \
  --target-margin 0.05 \
  --scopes fusion_head \
  --split-plan runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv \
  --group-weight-rows runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv \
  --split-offsets 0,1,2,3,4 \
  --baseline-repeat-run-dir runs/m1302_source_history_trainable_scope_repeat_probe \
  --robust-minfold \
  --bucket-columns source_family_pair,probe_template,margin_bucket \
  --lambda-bucket-cvar 2.0 \
  --lambda-retention 2.0 \
  --retention-margin-eps 0.02 \
  --minfold-temperature 0.25
```

## Probe Result

```text
result_class: source_history_trainable_scope_repeat_strong
best_repeat_offset_pass_count: 3
best_repeat_required_pass_count: 3
best_repeat_mean_eval_both_directional_fraction: 0.2517857143
best_repeat_mean_eval_group_all_rows_both_positive_fraction: 0.2517857143
best_repeat_mean_full_both_positive_count: 40.8
best_repeat_mean_full_group_all_rows_both_positive_count: 20.4
baseline_pass_offsets: 0|1|3
current_pass_offsets: 2|3|4
baseline_pass_lost_offsets: 0|1
top_failed_combo_positive_delta: +6
forbidden_parameter_mutation_detected: false
pair_specific_weight_used: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

This passes the aggregate repeat-strong classifier, but fails the M1311
lexicographic acceptance rule because baseline pass offsets `0` and `1` are
lost.

## Tradeoff Audit

M1312 also ran the M1310 tradeoff audit against M1302:

```text
result_class: weighted_repeat_tradeoff_nonregressive
baseline_repeat_offset_pass_count: 3
weighted_repeat_offset_pass_count: 3
offset_pass_count_delta: 0
new_pass_offsets: 2|4
lost_pass_offsets: 0|1
eval_improved_offsets: 2|4
eval_regressed_offsets: 0|1|3
mean_eval_both_directional_fraction_delta: +0.0182539683
mean_full_both_positive_count_delta: +2.8
full_baseline_positive_count: 95
full_weighted_positive_count: 102
full_improved_to_positive_count: 33
full_regressed_from_positive_count: 26
full_mean_margin_delta: +0.0183538462
top_failed_combo_positive_delta: +6
top_failed_combo_mean_margin_delta: +0.0019678615
```

Compared to M1309, this is a real improvement: aggregate repeat metrics and top
failed combo both improve. The remaining problem is not a missing signal; it is
surface swapping. The objective repairs failed folds by sacrificing previously
passing folds.

## Interpretation

Supported:

```text
Robust bucket/CVaR plus retention is a better direction than M1309 simple
weighted mean.
```

Supported:

```text
The top failed combo is now improved more strongly: M1309 had +3 positives;
M1312 has +6 positives.
```

Supported:

```text
Aggregate full positive groups improve from M1302: 95 -> 102.
```

Falsified:

```text
The current retention term is sufficient to preserve M1302 passing folds.
```

Falsified:

```text
Aggregate repeat-strong classification is enough for acceptance.
```

Not tested:

```text
Closed-loop replay retention, private holdout, public-gate checkpoint
promotion, high-fidelity simulation, real-vehicle transfer, or level3
self-identification.
```

## Failure Taxonomy

Primary:

```text
objective_overfit
```

Reason:

```text
The objective improves global averages and failed folds while losing baseline
passing folds.
```

Secondary:

```text
scenario_sampling_failure risk
```

Reason:

```text
The fixed split/corpus still allows pass-surface swapping across offsets.
```

Not observed:

```text
contract_violation
forbidden_parameter_mutation
pair_specific_weighting
private_holdout_contamination
promotion_gate_failure
training_instability
```

## Next Step

M1313 should audit this mixed result before another implementation. The likely
next route is a stricter lexicographic repair:

```text
first protect baseline passing offsets 0|1|3;
then optimize failed offsets 2|4;
reject candidates that swap pass surfaces.
```

Do not run PPO or promote from M1312.
