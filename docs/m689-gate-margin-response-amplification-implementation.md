# M689 Gate-Margin Response-Amplification Implementation

## Purpose

M689 implements the gate-margin response-amplification objective designed in
M688.

It extends the split/gated head with:

```text
detached-normal wrong-vs-normal gate margin
hard low-gate wrong-row pressure
stronger wrong gate-open pressure
gate-margin diagnostics
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

## Implementation Cleanliness

M689 is implementation-clean:

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

The base actor checksum is unchanged. Only gated residual-head checkpoints are
written.

## Exact Gate Result

M689 passes the exact actor-coupling gate:

```text
actor_coupling_exact_passed: true
passed_seed_count:           3
passed_seeds:                6890, 6891, 6892
best_selected_alpha:         1.0
```

## Source-Holdout Selected Alpha Result

All three seeds pass at `alpha=1.0`:

| seed | normal mean | normal p95 | gap mean | gap p10 | gap ratio | wrong MSE improvement | first drift p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6890 | 0.001441 | 0.002308 | 0.011040 | 0.008670 | 3.842495 | 0.782311 | 0.003858 |
| 6891 | 0.001380 | 0.002291 | 0.011165 | 0.008829 | 3.885905 | 0.795998 | 0.004017 |
| 6892 | 0.001461 | 0.002326 | 0.010731 | 0.008479 | 3.734864 | 0.791428 | 0.003748 |

Exact thresholds:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse_improvement >= 0.50
normal_action_drift_first_l2_p95 <= 0.0060
```

## Gate Diagnostics

Gate-margin pressure opens wrong gates enough to pass exact output gates:

```text
source-holdout alpha=1.0 normal_gate_mean: 0.440435 - 0.453106
source-holdout alpha=1.0 wrong_gate_mean:  0.503564 - 0.515852
source-holdout alpha=1.0 wrong_gate_margin_mean: 0.061641 - 0.063130
```

However, the gate factorization is not as clean as the design target:

```text
target wrong_gate_margin: 0.30
observed source-holdout margin mean: about 0.062
observed source-holdout margin p10: about -0.046
```

Normal retention passes because the normal raw amplifier is small, not because
the normal gate is near zero:

```text
normal_raw_sequence_l2_mean: 0.003116 - 0.003308
wrong_raw_sequence_l2_mean:  0.020149 - 0.020593
normal_gate_mean:           0.435924 - 0.448252
wrong_gate_mean:            0.532601 - 0.544602
```

## Comparison to M686

M686:

```text
normal retention: strong
wrong gate mean:  about 0.102 - 0.105
wrong gap mean:   about 0.0064
exact pass:       false
```

M689:

```text
normal retention: strong
wrong gate mean:  about 0.503 - 0.516 on source holdout
wrong gap mean:   about 0.0107 - 0.0112
exact pass:       true for 3/3 seeds
```

So gate-margin pressure fixes the output-level exact gate failure.

## Classification

Primary classification:

```text
exact_gate_pass_with_gate_diagnostic_caveat
```

Secondary labels:

```text
implementation_clean
normal_retention_positive
wrong_gap_restored
gate_margin_output_positive
normal_gate_not_closed
diagnostic_only_not_promoted
```

## Interpretation

M689 is a meaningful positive result for the response-amplification branch:

```text
the gated residual diagnostic head can satisfy normal retention and
wrong-history amplification exact gates simultaneously across 3 seeds.
```

It should not be described as a deployable driver result. The base actor is
unchanged, no PPO was used, and no checkpoint was promoted.

It should also not be overclaimed as clean gate-based self-identification,
because the normal gate remains moderately open and the margin target is not
fully reached. The effective mechanism is output-level separation through both
gate and raw amplifier, with exact behavior metrics passing.

## Decision

```text
gate_margin_response_amplification_exact_gate_passed_admit_audit
```

## Next

```text
m690-gate-margin-response-amplification-audit
```
