# M680 Branch-Specific Response-Amplification Implementation

## Purpose

M680 implements the branch-specific response-amplification objective designed in
M679. It extends the frozen-backbone actor-coupling probe with:

```text
detached-normal wrong-history first-gap loss
detached-normal wrong-history sequence-gap loss
hard low-gap row pressure
stronger wrong-target coefficient
existing normal first-step safety terms
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
  --seeds 6800,6801,6802 \
  --alphas 0.02,0.05,0.10,0.20,0.50,1.00 \
  --target-gap 0.010 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
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
  --run-dir runs/m680_branch_specific_response_amplification
```

## Implementation Cleanliness

M680 is implementation-clean:

```text
rows:                           648
source_count:                   216
branch_specific_gap:            true
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

## Exact Gate Result

M680 still fails the exact gate:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

But it changes the failure shape relative to M677.

## What Improved

Branch-specific wrong-history pressure restores much of the wrong-history gap:

```text
M677 alpha=1.0 gap mean: 0.0036 - 0.0069
M680 alpha=1.0 gap mean: 0.0082 - 0.0106
```

Seed `6801` reaches the wrong-history gap gates at `alpha=1.0`:

```text
gap mean:        0.010645
gap p10:         0.007573
gap ratio:       3.704878
wrong MSE improvement: 0.560882
first drift p95: 0.004210
```

So detached-normal branch-specific pressure is moving in the intended
direction.

## What Still Fails

The new blocker is normal full-sequence retention, not first-step drift.

At `alpha=1.0`:

| seed | normal mean | normal p95 | gap mean | gap ratio | first drift p95 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6800 | 0.004284 | 0.007710 | 0.008227 | 2.863412 | 0.004569 |
| 6801 | 0.003753 | 0.005652 | 0.010645 | 3.704878 | 0.004210 |
| 6802 | 0.003608 | 0.006227 | 0.009095 | 3.165607 | 0.004338 |

The exact gate requires:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
```

Seed `6801` satisfies the gap, p10, ratio, wrong-target, and first-drift gates,
but fails normal mean. Seed `6802` is close on gap and normal p95 but still
fails normal mean. Seed `6800` fails both gap and normal retention.

## Classification

M680 should be classified as:

```text
branch_specific_gap_partial_normal_sequence_retention_failure
```

Secondary labels:

```text
implementation_clean
exact_gate_failure
wrong_gap_partially_restored
first_step_safety_retained
normal_sequence_mean_regression
```

This is progress over M677:

```text
M677: first-step safe, gap suppressed.
M680: first-step safe, gap partially restored, but normal full sequence moved.
```

## Interpretation

The current branch-specific objective correctly shifts pressure toward the
wrong-history branch, but shared-head training still leaks enough residual into
normal-history sequence outputs to fail exact normal retention.

The next design should preserve the M680 wrong-branch pressure but add
normal-sequence safety, not just first-step safety.

Likely next direction:

```text
normal sequence top-k hinge / p95 pressure;
explicit normal sequence mean penalty;
possibly a gated or split residual architecture where the wrong-amplifier branch
is forced to stay inactive on normal-history features.
```

## Decision

```text
branch_specific_response_amplification_exact_gate_failed_admit_audit
```

## Next

```text
m681-branch-specific-response-amplification-audit
```
