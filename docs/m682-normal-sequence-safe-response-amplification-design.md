# M682 Normal-Sequence-Safe Response-Amplification Design

## Purpose

M682 designs the next exact actor-coupling probe after M680 partially restored
wrong-history gap but failed full normal-sequence retention.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Blocker Being Addressed

M680 branch-specific pressure improved wrong-history gap, especially seed
`6801`:

```text
alpha=1.0 gap mean:                 0.010645
alpha=1.0 gap p10:                  0.007573
alpha=1.0 gap ratio:                3.704878
alpha=1.0 wrong target improvement: 0.560882
alpha=1.0 first drift p95:          0.004210
```

But it failed normal full-sequence retention:

```text
normal_delta_l2_mean: 0.003753
gate:                 <= 0.0025
```

The next design should keep the wrong-history branch pressure while explicitly
constraining normal sequence residuals.

## Design Change

M683 should keep:

```text
frozen BC5660 backbone
fused_plus_next_hidden feature view
residual sequence head
first-residual execution
detached-normal branch-specific wrong-history gap losses
hard low-gap wrong-history row pressure
alpha ladder
exact source-heldout gates
no PPO
no promotion
```

It should add full normal-sequence retention terms:

```text
L_normal_sequence_mean_hinge
L_normal_sequence_topk_hinge
```

## Loss

M683 should train:

```text
L =
  L_normal_sequence_zero
  + lambda_normal_seq_mean * L_normal_sequence_mean_hinge
  + lambda_normal_seq_topk * L_normal_sequence_topk_hinge
  + lambda_normal_first * L_normal_first_zero
  + lambda_normal_first_topk * L_normal_first_topk_hinge
  + lambda_wrong * L_wrong_sequence_target
  + lambda_wrong_first * L_wrong_first_detached_gap
  + lambda_wrong_sequence_gap * L_wrong_sequence_detached_gap
  + lambda_wrong_hard * L_wrong_hard_rows
  + lambda_smooth * L_sequence_smoothness
```

Definitions:

```text
normal_sequence_l2(row) =
  mean_t ||pred_normal[t]||

L_normal_sequence_mean_hinge =
  max(0, weighted_mean(normal_sequence_l2) - normal_sequence_mean_threshold)^2

L_normal_sequence_topk_hinge =
  mean(topk(max(0, normal_sequence_l2 - normal_sequence_topk_threshold)^2))
```

Initial coefficients:

```text
lambda_normal_seq_mean: 4.0
lambda_normal_seq_topk: 2.0
lambda_normal_first:    5.0
lambda_normal_first_topk: 2.0
lambda_wrong:           2.0
lambda_wrong_first:     1.0
lambda_wrong_sequence_gap: 1.0
lambda_wrong_hard:      0.5
lambda_smooth:          0.05
```

Initial thresholds:

```text
normal_sequence_mean_threshold: 0.0020
normal_sequence_topk_threshold: 0.0045
normal_sequence_topk_fraction:  0.10
normal_first_threshold:         0.004
normal_first_topk_fraction:     0.10
wrong_first_target_gap:         0.006
wrong_sequence_target_gap:      0.012
wrong_hard_fraction:            0.25
```

The mean threshold is below the exact gate `0.0025` to create margin rather
than train exactly on the boundary.

## Exact Gates

Do not change the gates:

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

## Implementation Notes

Extend `autodrift.response_amplification_actor_coupling` with:

```text
--normal-sequence-mean-coef
--normal-sequence-mean-threshold
--normal-sequence-topk-coef
--normal-sequence-topk-threshold
--normal-sequence-topk-fraction
```

When coefficients are zero, the path remains compatible with M674-M680.

## Expected Outcome

Positive result:

```text
at least one seed passes at alpha > 0;
normal sequence mean <= 0.0025;
normal first drift p95 <= 0.006;
wrong-history gap mean >= 0.010;
actor checksum unchanged.
```

Negative result taxonomy:

```text
wrong_gap_suppressed_by_normal_sequence_anchor:
  normal sequence safety succeeds but gap falls below threshold.

normal_sequence_still_fails:
  new normal sequence pressure is too weak.

shared_head_capacity_conflict:
  neither side can satisfy both gates with a single residual head.
```

If M683 fails because normal and wrong objectives still conflict, the next
branch should consider a split or gated wrong-amplifier architecture.

## Decision

```text
normal_sequence_safe_response_amplification_design_admit_m683
```

## Next

```text
m683-normal-sequence-safe-response-amplification-implementation
```
