# M677 First-Step-Safe Response-Amplification Implementation

## Purpose

M677 implements the first-step-safe residual objective designed in M676. It
extends the M674 frozen-backbone residual sequence-head probe with:

```text
normal first residual anchor
normal first residual top-k/p95 hinge
wrong-history first-gap hinge
M671 wrong-history sequence target
alpha ladder exact evaluation
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
  --seeds 6770,6771,6772 \
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
  --wrong-first-gap-coef 0.25 \
  --wrong-first-target-gap 0.006 \
  --device cpu \
  --run-dir runs/m677_first_step_safe_response_amplification
```

## Implementation Cleanliness

M677 is implementation-clean:

```text
rows:                           648
source_count:                   216
residual_head_checkpoint_count: 3
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
ppo_used:                       false
promoted:                       false
```

## Exact Gate Result

M677 fails the exact gate:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

## What Improved

The first-step-safe objective successfully reduced first-action normal drift.
At `alpha=1.0`:

```text
M674 first drift p95: 0.0094 - 0.0130
M677 first drift p95: 0.0025 - 0.0033
```

So the new normal first-step terms work as intended.

## What Regressed

The wrong-history sequence gap collapsed. At `alpha=1.0`:

```text
M674 gap mean: 0.0121 - 0.0124
M677 gap mean: 0.0036 - 0.0069

M674 gap ratio: 4.2+
M677 gap ratio: 1.25 - 2.40
```

Source-heldout comparison:

| run | seed | alpha | normal mean | gap mean | gap ratio | first drift p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M674 | 6740 | 1.00 | 0.002394 | 0.012119 | 4.217997 | 0.009719 |
| M674 | 6741 | 1.00 | 0.002657 | 0.012412 | 4.320051 | 0.009403 |
| M674 | 6742 | 1.00 | 0.002699 | 0.012189 | 4.242287 | 0.012962 |
| M677 | 6770 | 1.00 | 0.003104 | 0.006888 | 2.397434 | 0.003332 |
| M677 | 6771 | 1.00 | 0.003118 | 0.005817 | 2.024605 | 0.002941 |
| M677 | 6772 | 1.00 | 0.003579 | 0.003593 | 1.250464 | 0.002471 |

The normal first-action safety objective overcorrected: it made the executable
first residual safe, but it suppressed the wrong-history residual too much.

## Classification

M677 should be classified as:

```text
first_step_safety_positive_wrong_gap_suppressed
```

Secondary labels:

```text
implementation_clean
exact_gate_failure
normal_first_drift_fixed
wrong_gap_failure_at_safe_alpha
objective_overfit
```

This is a better failure than M674 because it proves the first-step safety terms
control the intended metric. The remaining issue is maintaining wrong-history
separation under that safety constraint.

## Interpretation

M674 and M677 now bracket the tradeoff:

```text
M674:
  enough wrong-history gap;
  unsafe first normal residual.

M677:
  safe first normal residual;
  insufficient wrong-history gap.
```

The next design should decouple normal first-step safety from wrong-history
separation more explicitly. A likely direction is a branch-contrast loss that
protects normal first residual while applying stronger wrong-history first and
sequence pressure only on variant hidden states.

## Decision

```text
first_step_safe_response_amplification_exact_gate_failed_admit_audit
```

## Next

```text
m678-first-step-safe-response-amplification-audit
```
