# M676 First-Step-Safe Response-Amplification Design

## Purpose

M676 designs the next actor-coupling probe after M674/M675 exposed a
first-action drift versus sequence-gap conflict.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Blocker Being Addressed

M674 trained a residual sequence head that could create wrong-history sequence
gap at `alpha=1.0`, but the first executed normal residual was too large:

```text
alpha=1.0:
  gap mean:       ~0.0121-0.0124
  gap ratio:      ~4.2
  first drift p95: 0.0094-0.0130  # fails <= 0.006

alpha=0.5:
  first drift p95: 0.0047-0.0065
  gap mean:        ~0.0061        # fails >= 0.010
  gap ratio:       ~2.1           # fails >= 3.0
```

So the residual head has representation signal, but the training objective does
not make the first executed residual safe enough.

## Design Change

M677 should keep the frozen-backbone residual structure:

```text
base actor: frozen BC5660
feature view: fused_plus_next_hidden
trainable: residual sequence head only
execution: first residual only
```

But it should replace the generic sequence objective with a first-step-safe
objective.

## Loss

M677 should train:

```text
L =
  L_normal_sequence_zero
  + lambda_normal_first * L_normal_first_zero
  + lambda_normal_topk * L_normal_first_topk_hinge
  + lambda_wrong * L_wrong_sequence_target
  + lambda_wrong_first * L_wrong_first_min_gap
  + lambda_gap * L_sequence_gap_margin
  + lambda_smooth * L_sequence_smoothness
```

Definitions:

```text
L_normal_sequence_zero:
  masked MSE over the full normal residual sequence against zero.

L_normal_first_zero:
  MSE of normal first residual against zero.

L_normal_first_topk_hinge:
  top-k squared hinge on normal first residual L2:
    mean(topk(max(0, first_l2 - first_threshold)^2))
  This approximates the p95 gate during training.

L_wrong_sequence_target:
  masked MSE against M671 target_delta_wrong.

L_wrong_first_min_gap:
  hinge that encourages wrong-history first residual gap:
    max(0, wrong_first_target_gap - ||wrong_first - normal_first||)^2
  This keeps first-step wrong-history signal from vanishing when normal first
  residual is strongly anchored.

L_sequence_gap_margin:
  same source-heldout diagnostic sequence-gap pressure as M674.

L_sequence_smoothness:
  small adjacent-step residual smoothness penalty.
```

Initial coefficients:

```text
lambda_normal_first: 5.0
lambda_normal_topk:  2.0
lambda_wrong:        1.0
lambda_wrong_first:  0.25
lambda_gap:          0.25
lambda_smooth:       0.05
```

Initial first-step thresholds:

```text
normal_first_threshold: 0.004
normal_first_topk_fraction: 0.10
wrong_first_target_gap: 0.006
```

These are deliberately conservative: the exact gate remains
`normal_action_drift_first_l2_p95 <= 0.006`, but training starts penalizing rows
before they reach the hard gate.

## Alpha Ladder

Keep the M674 ladder:

```text
alpha: 0.02, 0.05, 0.10, 0.20, 0.50, 1.00
```

M677 should select the largest passing alpha. A useful positive result would be:

```text
alpha >= 0.5 passes;
normal first-action p95 <= 0.006;
source-heldout sequence gap mean >= 0.010;
gap ratio >= 3.0.
```

If only very small alphas pass, classify as `wrong_gap_failure_at_safe_alpha`.

## Exact Pass Criteria

Use the same exact actor-coupling criteria as M674:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse_improvement >= 0.50
normal_action_drift_first_l2_p95 <= 0.0060 at selected alpha
actor_checksum unchanged
no base actor checkpoint written
no PPO
```

Do not weaken the normal first-action drift gate.

## Implementation Notes

M677 can extend `autodrift.response_amplification_actor_coupling` rather than
creating a separate incompatible path. It should add:

```text
--normal-first-coef
--normal-first-topk-coef
--normal-first-threshold
--normal-first-topk-fraction
--wrong-first-gap-coef
--wrong-first-target-gap
```

Required artifacts:

```text
runs/m677_first_step_safe_response_amplification/summary.json
runs/m677_first_step_safe_response_amplification/alpha_summary.csv
runs/m677_first_step_safe_response_amplification/seed_view_summary.csv
docs/m677-first-step-safe-response-amplification-implementation.md
```

## Negative Result Interpretation

If M677 fails:

```text
normal first drift still fails:
  first-step anchor is too weak or representation entangles normal/wrong
  residuals too strongly.

safe alphas pass first drift but fail sequence gap:
  executable wrong-history residual may need different target construction.

train passes but source-heldout fails:
  first-step-safe objective overfits source rows.
```

## Decision

```text
first_step_safe_response_amplification_design_admit_m677
```

## Next

```text
m677-first-step-safe-response-amplification-implementation
```
