# M1362 Paper-Route Bidirectional Active-Set Interpolation Preflight

## Summary

M1362 ran an exact-plus-replay interpolation preflight from M1154 to the raw
M1360 bidirectional active-set checkpoint.

Decision:

```text
bidirectional_active_set_interpolation_preflight_pass_route_to_result_audit
```

The preflight found a replay-safe trust-region alpha:

```text
selected_alpha: 0.1
selected_checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

This is not a promotion. It has passed exact metrics plus two public replay
preflight surfaces only.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.materialized_source_history_interpolation_preflight \
  --base-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m1360_bidirectional_active_set_probe/checkpoints/raw_bidirectional_active_set_update.pt \
  --run-dir runs/m1362_bidirectional_active_set_interpolation_preflight \
  --device cpu \
  --alphas 0.005,0.01,0.02,0.05,0.1,0.2,0.4,0.6,0.8,1.0
```

## Result

Summary:

```text
result_class: materialized_source_history_interpolation_preflight_pass
exact_candidate_count: 10 / 10
M267/M264 pass count: 9 / 10
M183/M170 pass count: 5 / 9
selected_alpha: 0.1
preflight_pass: true
```

Selected alpha exact metrics:

```text
combined_loss_delta_vs_base: -0.5148637349
group_min_joint_margin_delta_vs_base: +0.5245143565
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667957
```

Selected alpha M267/M264:

```text
gate_pass: true
normal_success_delta: 0.0
success_drop_count_delta: 0
normal_margin_mean_delta: -0.0006892337
margin_gap_mean_delta: -0.0001940233
```

Selected alpha M183/M170:

```text
gate_pass: true
normal_success_delta: 0.0
success_drop_count_delta: 0
normal_margin_mean_delta: -0.0009321318
margin_gap_mean_delta: -0.0002484803
```

Raw alpha `1.0` remains rejected:

```text
M267/M264 gate_pass: false
M267/M264 margin_gap_mean_delta: -0.0012517700
```

Alphas `0.2`, `0.4`, `0.6`, and `0.8` pass M267/M264 but fail M183/M170, mainly
through old-surface normal success and success-drop regressions.

## Interpretation

M1362 confirms M1361's audit: the raw M1360 direction is useful, but the update
amplitude must be bounded.

Compared with the older M1352 diagnostic alpha `0.005`, the selected M1362 alpha
`0.1` is materially stronger:

```text
M1352 selected combined delta: -0.0317072824
M1362 selected combined delta: -0.5148637349

M1352 selected group-min delta: +0.0322478571
M1362 selected group-min delta: +0.5245143565
```

The M1362 selected checkpoint also preserves both current-family and old-family
public replay preflight surfaces. It should therefore route to a result audit and
then a carefully scoped next gate. It should not be promoted directly.

## Guardrails

M1362 performs no training, PPO, actor update, private holdout, promotion, full
public replay, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1363-paper-route-bidirectional-interpolation-result-audit
```
