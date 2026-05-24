# M686 Split-Gated Response-Amplification Implementation

## Purpose

M686 implements the split/gated response-amplification exact probe designed in
M685.

It adds an optional gated residual head:

```text
raw_sequence = max_residual * tanh(amplifier(feature))
gate         = sigmoid(gate_net(feature))
residual     = gate * raw_sequence
```

The legacy MLP head remains the default path. The gated path is enabled only by:

```text
--head-type gated
```

This milestone remains diagnostic:

```text
no PPO
no base actor update
no base actor checkpoint
no promotion
```

## Command

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

## Implementation Cleanliness

M686 is implementation-clean:

```text
rows:                           648
source_count:                   216
head_type:                      gated
max_residual:                   0.04
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

Gate diagnostics are written to seed summaries, alpha summaries, and train
metrics.

## Exact Gate Result

M686 does not pass the exact actor-coupling gate:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## Source-Holdout Alpha Result

At `alpha=1.0`:

| seed | normal mean | normal p95 | gap mean | gap p10 | gap ratio | wrong MSE improvement | first drift p95 | normal gate mean | wrong gate mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6860 | 0.001159 | 0.002524 | 0.006386 | 0.004356 | 2.222601 | 0.195735 | 0.002593 | 0.098797 | 0.104148 |
| 6861 | 0.001097 | 0.002386 | 0.006407 | 0.004445 | 2.230054 | 0.198466 | 0.002715 | 0.098005 | 0.102236 |
| 6862 | 0.001152 | 0.002562 | 0.006416 | 0.004164 | 2.233034 | 0.204071 | 0.002713 | 0.097119 | 0.101224 |

Exact gate thresholds remain:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse_improvement >= 0.50
normal_action_drift_first_l2_p95 <= 0.0060
```

## What Improved

The gated head strongly improves normal-history retention:

```text
M683 best alpha=1.0 normal mean: 0.002769
M686 best alpha=1.0 normal mean: 0.001097
```

Normal p95 and first drift are also comfortably inside gates.

The raw amplifier has enough amplitude:

```text
wrong_raw_sequence_l2_mean: 0.060179 - 0.062896
```

So this is not a bounded-amplifier capacity failure.

## What Failed

The gate collapses near the normal threshold for both branches:

```text
normal_gate_mean: 0.097540 - 0.098755
wrong_gate_mean:  0.102354 - 0.104949
```

The wrong gate does not open toward the target `0.50`; final
`wrong_gate_open_hinge` remains around:

```text
0.155994 - 0.159119
```

Because the wrong gate stays near `0.10`, the large raw amplifier is attenuated
to a wrong-history gap around `0.0064`, below the `0.010` exact threshold.

## Classification

M686 should be classified as:

```text
gate_collapse
```

Secondary labels:

```text
implementation_clean
normal_retention_strong_positive
wrong_gate_open_failure
wrong_gap_below_threshold
not_amplifier_capacity_failure
```

## Interpretation

The split/gated architecture solves the normal-retention side too well: the
normal gate close loss pushes the shared gate decision down, and the current
wrong gate open pressure is too weak to make wrong-history features open.

The next step should not remove the gate or weaken normal gates. It should
audit whether gate separation needs:

```text
stronger wrong gate-open pressure;
explicit wrong-vs-normal gate margin;
hard low-gate wrong rows;
or a separate gate objective schedule.
```

## Decision

```text
split_gated_response_amplification_exact_gate_failed_admit_audit
```

## Next

```text
m687-split-gated-response-amplification-audit
```
