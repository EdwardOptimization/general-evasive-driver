# M683 Normal-Sequence-Safe Response-Amplification Implementation

## Purpose

M683 implements the normal-sequence-safe branch-specific response-amplification
objective designed in M682.

It extends the frozen-backbone actor-coupling probe with:

```text
normal full-sequence mean hinge
normal full-sequence top-k hinge
existing normal first-step safety terms
detached-normal branch-specific wrong-history first/sequence gap losses
hard low-gap wrong-history row pressure
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
  --seeds 6830,6831,6832 \
  --alphas 0.02,0.05,0.10,0.20,0.50,1.00 \
  --target-gap 0.010 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --normal-sequence-mean-coef 4.0 \
  --normal-sequence-mean-threshold 0.002 \
  --normal-sequence-topk-coef 2.0 \
  --normal-sequence-topk-threshold 0.0045 \
  --normal-sequence-topk-fraction 0.10 \
  --normal-first-coef 5.0 \
  --normal-first-topk-coef 2.0 \
  --normal-first-threshold 0.004 \
  --normal-first-topk-fraction 0.10 \
  --wrong-target-coef 2.0 \
  --wrong-first-gap-coef 1.0 \
  --wrong-first-target-gap 0.006 \
  --branch-specific-gap \
  --wrong-sequence-gap-coef 1.0 \
  --wrong-sequence-target-gap 0.012 \
  --wrong-hard-coef 0.5 \
  --wrong-hard-fraction 0.25 \
  --device cpu \
  --run-dir runs/m683_normal_sequence_safe_response_amplification
```

## Implementation Cleanliness

M683 is implementation-clean:

```text
rows:                           648
source_count:                   216
residual_head_checkpoint_count: 3
branch_specific_gap:            true
normal_sequence_mean_coef:      4.0
normal_sequence_topk_coef:      2.0
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

The base actor checksum is unchanged. Only residual sequence heads are written.

## Exact Gate Result

M683 does not pass the exact actor-coupling gate:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## Source-Holdout Alpha Result

At `alpha=1.0`:

| seed | normal mean | normal p95 | gap mean | gap p10 | gap ratio | wrong MSE improvement | first drift p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6830 | 0.002769 | 0.004459 | 0.006909 | 0.005181 | 2.404847 | 0.339317 | 0.004284 |
| 6831 | 0.002886 | 0.004277 | 0.008320 | 0.005536 | 2.895718 | 0.438964 | 0.004269 |
| 6832 | 0.002958 | 0.004624 | 0.007888 | 0.005132 | 2.745395 | 0.415933 | 0.004282 |

Gate thresholds:

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

Normal full-sequence retention improved relative to M680.

M680 best branch-specific seed:

```text
seed 6801 alpha=1.0 normal_delta_l2_mean: 0.003753
```

M683 best normal-sequence-safe seed:

```text
seed 6830 alpha=1.0 normal_delta_l2_mean: 0.002769
```

Normal p95 and first drift are now comfortably inside their gates at
`alpha=1.0` for all three seeds.

## What Regressed

Wrong-history gap is suppressed by the normal-sequence anchor.

M680 best branch-specific seed:

```text
seed 6801 alpha=1.0 gap mean:                 0.010645
seed 6801 alpha=1.0 gap ratio:                3.704878
seed 6801 alpha=1.0 wrong MSE improvement:    0.560882
```

M683 best normal-sequence-safe seed:

```text
seed 6831 alpha=1.0 gap mean:                 0.008320
seed 6831 alpha=1.0 gap ratio:                2.895718
seed 6831 alpha=1.0 wrong MSE improvement:    0.438964
```

At lower alphas, normal sequence retention passes, but wrong-history gap is far
below threshold. At `alpha=1.0`, wrong-history gap is still below threshold and
normal mean is still slightly above the gate.

## Classification

M683 should be classified as:

```text
wrong_gap_suppressed_by_normal_sequence_anchor
```

Secondary labels:

```text
implementation_clean
exact_gate_failure
normal_sequence_retention_improved
wrong_history_gap_regressed
shared_head_capacity_conflict_possible
```

## Interpretation

M683 confirms that normal sequence retention pressure is active and useful, but
the single residual head still trades off normal-history inactivity against
wrong-history amplification.

The result is not a reason to loosen gates or run PPO. It suggests the next
audit should decide whether this is still tunable by scalar coefficients or is
better treated as a structural issue requiring a split or gated wrong-amplifier
path.

## Decision

```text
normal_sequence_safe_response_amplification_exact_gate_failed_admit_audit
```

## Next

```text
m684-normal-sequence-safe-response-amplification-audit
```
