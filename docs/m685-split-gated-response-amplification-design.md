# M685 Split-Gated Response-Amplification Design

## Purpose

M685 designs the next exact actor-coupling probe after M683 showed that scalar
loss balancing is not enough:

```text
M680: wrong-history gap can be restored, but normal sequence residual moves.
M683: normal sequence residual improves, but wrong-history gap is suppressed.
```

The next probe should separate:

```text
when to activate a residual
what residual sequence to emit
```

without changing actor inputs, running PPO, writing a base actor checkpoint, or
promoting a checkpoint.

## Design Summary

M686 should add an optional gated residual head:

```text
raw_sequence = max_residual * tanh(amplifier(feature))
gate         = sigmoid(gate_net(feature))
residual     = gate * raw_sequence
```

Initial implementation should use a sequence-level scalar gate:

```text
gate shape: [batch, 1, 1]
raw_sequence shape: [batch, horizon, action_dim]
```

The scalar gate keeps the first implementation simple and makes diagnostics
easy:

```text
normal_gate_mean
normal_gate_p95
wrong_gate_mean
wrong_gate_p10
```

The head remains diagnostic:

```text
frozen BC5660 actor backbone
fused_plus_next_hidden features
train only residual-head/gate parameters
execute only first residual in alpha ladder
no PPO
no base actor checkpoint
no promotion
```

## Why Gating

M683 tried to force a single MLP output to be:

```text
near zero on normal-history features
large enough on wrong-history features
```

with only scalar loss weights. The result improved normal sequence retention
but suppressed wrong-history gap. A gate gives the model a cleaner internal
factorization:

```text
normal branch:
  gate should close and residual should remain near zero

wrong-history branch:
  gate should open and amplifier should emit the target residual direction
```

This does not add labels to actor input. Normal/wrong branch labels are
training-time supervision for the diagnostic residual head only.

## Loss

M686 should preserve the M683 objective components:

```text
L_normal_sequence_mean_hinge
L_normal_sequence_topk_hinge
L_normal_first_zero
L_normal_first_topk_hinge
L_wrong_sequence_target
L_wrong_first_detached_gap
L_wrong_sequence_detached_gap
L_wrong_hard_rows
L_sequence_smoothness
```

and add:

```text
L_normal_gate_mean
L_normal_gate_topk
L_wrong_gate_open
L_raw_amplifier_l2
```

Definitions:

```text
L_normal_gate_mean =
  weighted_mean(gate_normal^2)

L_normal_gate_topk =
  mean(topk(max(0, gate_normal - normal_gate_threshold)^2))

L_wrong_gate_open =
  weighted_mean(max(0, wrong_gate_target - gate_wrong)^2)

L_raw_amplifier_l2 =
  weighted_mean(mean_t ||raw_sequence||^2)
```

`L_raw_amplifier_l2` is a guard against the degenerate solution:

```text
gate small, raw amplifier huge
```

The output should also be bounded:

```text
raw_sequence = max_residual * tanh(raw_sequence_logits)
```

Initial `max_residual`:

```text
0.04
```

## Initial Coefficients

Start conservative:

```text
normal_sequence_mean_coef:   4.0
normal_sequence_topk_coef:   2.0
normal_first_coef:           5.0
normal_first_topk_coef:      2.0
normal_gate_coef:            1.0
normal_gate_topk_coef:       1.0
wrong_target_coef:           2.0
wrong_first_gap_coef:        1.0
wrong_sequence_gap_coef:     1.0
wrong_hard_coef:             0.5
wrong_gate_open_coef:        0.25
raw_amplifier_l2_coef:       0.01
smoothness_coef:             0.05
```

Initial thresholds:

```text
normal_sequence_mean_threshold: 0.0020
normal_sequence_topk_threshold: 0.0045
normal_first_threshold:         0.0040
normal_gate_threshold:          0.10
normal_gate_topk_fraction:      0.10
wrong_first_target_gap:         0.006
wrong_sequence_target_gap:      0.012
wrong_hard_fraction:            0.25
wrong_gate_target:              0.50
```

## Exact Gates

Do not change the exact actor-coupling pass gates:

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

Gate diagnostics should be reported but not used as promotion evidence yet:

```text
normal_gate_mean
normal_gate_p95
wrong_gate_mean
wrong_gate_p10
```

## Implementation Notes

M686 should extend `autodrift.response_amplification_actor_coupling` with:

```text
--head-type mlp|gated
--max-residual
--normal-gate-coef
--normal-gate-topk-coef
--normal-gate-threshold
--normal-gate-topk-fraction
--wrong-gate-open-coef
--wrong-gate-target
--raw-amplifier-l2-coef
```

Default `--head-type mlp` should preserve M674-M683 behavior.

Implementation shape:

```text
class GatedResponseAmplifierHead(nn.Module):
    forward(features) -> residual
    forward_with_aux(features) -> residual, raw_sequence, gate
```

Loss code should use `forward_with_aux` when available and otherwise report
zero gate losses for the legacy MLP head.

The saved residual-head checkpoint should include:

```text
head_type
max_residual
gate_diagnostics_available
```

## M686 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.response_amplification_actor_coupling \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --shadow-corpus runs/m671_response_amplification_shadow/shadow_corpus.npz \
  --metadata runs/m671_response_amplification_shadow/shadow_metadata.csv \
  --view fused_plus_next_hidden \
  --seeds 6860,6861,6862 \
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
  --wrong-gate-open-coef 0.25 \
  --wrong-gate-target 0.50 \
  --raw-amplifier-l2-coef 0.01 \
  --device cpu \
  --run-dir runs/m686_split_gated_response_amplification
```

## Expected Outcomes

Positive result:

```text
at least one nonzero alpha passes exact source-holdout gates
normal gate closes on normal features
wrong gate opens enough to restore gap
base actor checksum unchanged
no base actor checkpoint written
no PPO
```

Negative result taxonomy:

```text
gate_collapse:
  normal and wrong gates both close, suppressing gap.

normal_gate_leak:
  wrong gap improves, but normal gate/residual leaks and normal retention fails.

amplifier_capacity_failure:
  gate separation works, but bounded raw amplifier cannot produce enough gap.

feature_overlap_structural_limit:
  gate cannot distinguish normal from wrong features under source-heldout split.
```

If M686 fails with `feature_overlap_structural_limit`, the next branch should
audit feature separation for the gated head before increasing loss weights.

## Decision

```text
split_gated_response_amplification_design_admit_m686
```

## Next

```text
m686-split-gated-response-amplification-implementation
```
