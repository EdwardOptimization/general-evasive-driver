# M688 Gate-Margin Response-Amplification Design

## Purpose

M688 designs the next split/gated exact probe after M686 showed:

```text
normal retention: strong positive
raw wrong amplifier: large enough
wrong gate: collapsed near normal gate
```

The next objective should explicitly open wrong-history gates relative to
normal-history gates rather than relying only on an absolute wrong-gate target.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
no actor-input change
```

## Blocker Being Addressed

M686 gate diagnostics:

```text
normal_gate_mean: 0.097540 - 0.098755
wrong_gate_mean:  0.102354 - 0.104949
wrong_gate_target: 0.50
```

The wrong gate is only slightly above the normal gate. Because the raw wrong
amplifier is already large:

```text
wrong_raw_sequence_l2_mean: 0.060179 - 0.062896
```

the main issue is gate activation, not amplifier capacity.

## Design Change

M689 should keep the split/gated head:

```text
raw_sequence = max_residual * tanh(amplifier(feature))
gate         = sigmoid(gate_net(feature))
residual     = gate * raw_sequence
```

and add two gate-specific losses:

```text
L_wrong_gate_margin
L_wrong_gate_hard
```

The normal gate should stay closed through the existing normal losses:

```text
L_normal_gate_mean
L_normal_gate_topk
L_normal_sequence_mean_hinge
L_normal_sequence_topk_hinge
L_normal_first_zero
L_normal_first_topk_hinge
```

## New Losses

### Detached-Normal Gate Margin

```text
L_wrong_gate_margin =
  weighted_mean(max(0, margin - (gate_wrong - detach(gate_normal)))^2)
```

This should move the wrong gate up without rewarding normal gate leakage.

Initial values:

```text
wrong_gate_margin_coef: 2.0
wrong_gate_margin:      0.30
```

### Hard Low-Gate Wrong Rows

Use the lowest wrong gates or lowest wrong-normal gate margins:

```text
hard_rows = bottom_k(gate_wrong - detach(gate_normal))
```

For those rows, apply stronger wrong-gate pressure:

```text
L_wrong_gate_hard =
  mean_hard(max(0, wrong_gate_target - gate_wrong)^2)
  + mean_hard(max(0, margin - (gate_wrong - detach(gate_normal)))^2)
```

Initial values:

```text
wrong_gate_hard_coef:     1.0
wrong_gate_hard_fraction: 0.25
```

## Full Objective

M689 should train:

```text
L =
  L_shadow_base
  + lambda_normal_seq_mean * L_normal_sequence_mean_hinge
  + lambda_normal_seq_topk * L_normal_sequence_topk_hinge
  + lambda_normal_gate * L_normal_gate_mean
  + lambda_normal_gate_topk * L_normal_gate_topk
  + lambda_normal_first * L_normal_first_zero
  + lambda_normal_first_topk * L_normal_first_topk_hinge
  + lambda_wrong_target * L_wrong_sequence_target
  + lambda_wrong_first * L_wrong_first_detached_gap
  + lambda_wrong_sequence * L_wrong_sequence_detached_gap
  + lambda_wrong_hard * L_wrong_hard_rows
  + lambda_wrong_gate_open * L_wrong_gate_open
  + lambda_wrong_gate_margin * L_wrong_gate_margin
  + lambda_wrong_gate_hard * L_wrong_gate_hard
  + lambda_raw_l2 * L_raw_amplifier_l2
  + lambda_smooth * L_sequence_smoothness
```

Initial coefficients:

```text
normal_sequence_mean_coef: 4.0
normal_sequence_topk_coef: 2.0
normal_gate_coef:          1.0
normal_gate_topk_coef:     1.0
normal_first_coef:         5.0
normal_first_topk_coef:    2.0
wrong_target_coef:         2.0
wrong_first_gap_coef:      1.0
wrong_sequence_gap_coef:   1.0
wrong_hard_coef:           0.5
wrong_gate_open_coef:      2.0
wrong_gate_margin_coef:    2.0
wrong_gate_hard_coef:      1.0
raw_amplifier_l2_coef:     0.01
smoothness_coef:           0.05
```

Initial thresholds:

```text
normal_sequence_mean_threshold: 0.0020
normal_sequence_topk_threshold: 0.0045
normal_first_threshold:         0.0040
normal_gate_threshold:          0.10
wrong_gate_target:              0.50
wrong_gate_margin:              0.30
wrong_first_target_gap:         0.006
wrong_sequence_target_gap:      0.012
wrong_hard_fraction:            0.25
wrong_gate_hard_fraction:       0.25
max_residual:                   0.04
```

## Exact Gates

Keep the same actor-coupling pass gates:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse_improvement >= 0.50
normal_action_drift_first_l2_p95 <= 0.0060
actor_checksum unchanged
no base actor checkpoint written
no PPO
```

Gate diagnostics should include:

```text
normal_gate_mean
normal_gate_p95
wrong_gate_mean
wrong_gate_p10
wrong_gate_margin_mean
wrong_gate_margin_p10
```

Gate diagnostics remain diagnostic only for this milestone.

## Implementation Notes

Extend `autodrift.response_amplification_actor_coupling` with:

```text
--wrong-gate-margin-coef
--wrong-gate-margin
--wrong-gate-hard-coef
--wrong-gate-hard-fraction
```

Default values should keep legacy MLP and M686 paths compatible:

```text
wrong_gate_margin_coef: 0.0
wrong_gate_hard_coef:   0.0
```

The implementation should report:

```text
wrong_gate_margin_hinge
wrong_gate_hard_loss
hard_gate_row_count
```

## M689 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.response_amplification_actor_coupling \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --shadow-corpus runs/m671_response_amplification_shadow/shadow_corpus.npz \
  --metadata runs/m671_response_amplification_shadow/shadow_metadata.csv \
  --view fused_plus_next_hidden \
  --seeds 6890,6891,6892 \
  --alphas 0.02,0.05,0.10,0.20,0.50,1.00 \
  --target-gap 0.010 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --head-type gated \
  --max-residual 0.04 \
  --normal-sequence-mean-coef 4.0 \
  --normal-sequence-mean-threshold 0.002 \
  --normal-sequence-topk-coef 2.0 \
  --normal-sequence-topk-threshold 0.0045 \
  --normal-sequence-topk-fraction 0.10 \
  --normal-first-coef 5.0 \
  --normal-first-topk-coef 2.0 \
  --normal-first-threshold 0.004 \
  --normal-first-topk-fraction 0.10 \
  --normal-gate-coef 1.0 \
  --normal-gate-topk-coef 1.0 \
  --normal-gate-threshold 0.10 \
  --normal-gate-topk-fraction 0.10 \
  --wrong-target-coef 2.0 \
  --wrong-first-gap-coef 1.0 \
  --wrong-first-target-gap 0.006 \
  --branch-specific-gap \
  --wrong-sequence-gap-coef 1.0 \
  --wrong-sequence-target-gap 0.012 \
  --wrong-hard-coef 0.5 \
  --wrong-hard-fraction 0.25 \
  --wrong-gate-open-coef 2.0 \
  --wrong-gate-target 0.50 \
  --wrong-gate-margin-coef 2.0 \
  --wrong-gate-margin 0.30 \
  --wrong-gate-hard-coef 1.0 \
  --wrong-gate-hard-fraction 0.25 \
  --raw-amplifier-l2-coef 0.01 \
  --device cpu \
  --run-dir runs/m689_gate_margin_response_amplification
```

## Expected Outcomes

Positive result:

```text
wrong_gate_mean increases materially above M686
wrong_gate_margin_mean becomes positive and source-heldout stable
normal retention remains inside gates
wrong-history gap reaches threshold at a nonzero alpha
base actor checksum unchanged
no PPO
```

Negative taxonomy:

```text
normal_gate_leak:
  wrong gate opens, but normal gate/residual also leaks and normal retention fails.

gate_margin_overpower:
  gate margin opens wrong gates but overshoots residual output so no alpha passes.

gate_margin_ineffective:
  wrong gate remains collapsed despite stronger margin and hard-row pressure.

feature_overlap_structural_limit:
  gate margin cannot separate source-heldout normal/wrong features.
```

## Decision

```text
gate_margin_response_amplification_design_admit_m689
```

## Next

```text
m689-gate-margin-response-amplification-implementation
```
