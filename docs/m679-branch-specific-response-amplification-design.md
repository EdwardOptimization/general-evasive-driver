# M679 Branch-Specific Response-Amplification Design

## Purpose

M679 designs the next exact actor-coupling probe after M677 fixed first-step
normal safety but suppressed wrong-history gap.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Blocker Being Addressed

M677 showed:

```text
normal first-step safety: fixed
wrong-history sequence gap: suppressed
```

Interpretation:

```text
the shared residual head can satisfy the normal branch,
but wrong-history branch pressure is too weak or too entangled with normal
zero-residual pressure.
```

The next objective should make the wrong-history branch carry the separation
while keeping normal first-step safety intact.

## Design Change

M680 should keep:

```text
base actor: frozen BC5660
feature view: fused_plus_next_hidden
trainable module: residual sequence head only
execution: first residual only
alpha ladder: 0.02, 0.05, 0.10, 0.20, 0.50, 1.00
actor input contract: unchanged P0 human-view
```

But it should change gap losses so they do not pull the normal branch away from
zero:

```text
gap_normal_ref = stop_gradient(pred_normal)
gap = ||pred_wrong - gap_normal_ref||
```

This is a branch-specific loss: normal branch is controlled by normal anchors;
wrong branch is responsible for creating separation.

## Loss

M680 should train:

```text
L =
  L_normal_sequence_zero
  + lambda_normal_first * L_normal_first_zero
  + lambda_normal_topk * L_normal_first_topk_hinge
  + lambda_wrong * L_wrong_sequence_target
  + lambda_wrong_first * L_wrong_first_detached_gap
  + lambda_wrong_sequence_gap * L_wrong_sequence_detached_gap
  + lambda_wrong_hard * L_wrong_hard_rows
  + lambda_smooth * L_sequence_smoothness
```

Definitions:

```text
L_wrong_first_detached_gap:
  hinge on ||pred_wrong_first - detach(pred_normal_first)||.

L_wrong_sequence_detached_gap:
  hinge on sequence mean L2 between pred_wrong and detach(pred_normal).

L_wrong_hard_rows:
  extra wrong-target/gap pressure on rows where prior M677 gap was lowest or
  where the current batch has smallest detached gap.
```

Initial coefficients:

```text
lambda_normal_first:       5.0
lambda_normal_topk:        2.0
lambda_wrong:              2.0
lambda_wrong_first:        1.0
lambda_wrong_sequence_gap: 1.0
lambda_wrong_hard:         0.5
lambda_smooth:             0.05
```

Initial thresholds:

```text
normal_first_threshold: 0.004
normal_first_topk_fraction: 0.10
wrong_first_target_gap: 0.006
wrong_sequence_target_gap: 0.012
wrong_hard_fraction: 0.25
```

The increased `lambda_wrong` is intentional. M677 proved that normal safety is
controllable; M680 should restore wrong-history pressure without moving the
normal branch.

## Hard-Row Weighting

Use current-batch hard rows first, because it avoids depending on an external
M677 row table alignment:

```text
row_gap = mean_l2(pred_wrong - detach(pred_normal))
hard_rows = lowest wrong_hard_fraction by row_gap
L_wrong_hard = wrong_target MSE + detached sequence-gap hinge on hard_rows
```

M680 should report whether hard-row pressure is active:

```text
wrong_hard_fraction
hard_row_count_train
hard_row_count_source_holdout
```

If this still fails, a later milestone can build a fixed hard-row corpus from
M677 alpha metrics.

## Exact Gates

Keep M674/M677 gates unchanged:

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

Do not weaken the safety gate.

## Implementation Notes

Extend `autodrift.response_amplification_actor_coupling` with:

```text
--branch-specific-gap
--wrong-sequence-gap-coef
--wrong-sequence-target-gap
--wrong-hard-coef
--wrong-hard-fraction
```

When `--branch-specific-gap` is disabled, behavior should remain compatible
with M674/M677.

## Expected Outcome

A positive result should look like:

```text
alpha >= 0.5 passes in at least 1 seed;
normal first-action drift p95 remains <= 0.006;
wrong-history gap mean returns to >= 0.010;
gap ratio >= 3.0;
actor checksum unchanged.
```

A negative result should classify which side failed:

```text
normal_safety_regression:
  branch-specific pressure still leaks into normal branch.

wrong_gap_still_suppressed:
  wrong branch cannot carry the separation with this shared head.

train_source_overfit:
  train passes but source-heldout fails.
```

## Decision

```text
branch_specific_response_amplification_design_admit_m680
```

## Next

```text
m680-branch-specific-response-amplification-implementation
```
