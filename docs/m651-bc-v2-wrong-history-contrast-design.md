# M651 BC-v2 Wrong-History Contrast Design

## Purpose

M651 designs a frozen-head contrast objective after M650 showed that the
source-balanced sequence-delta head is learnable but nearly invariant to
wrong-history recurrent state.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Blocker From M650

M649 best-validation heads predict almost the same correction for normal and
wrong-history features:

```text
source 30 gap_l2: 0.000648 / 0.000704 / 0.000651
source 32 gap_l2: 0.000596 / 0.000598 / 0.000526
```

This means the head learned a generic local correction, not a history-sensitive
correction. Actor coupling remains blocked until the head objective can make
the wrong-history branch distinct.

## Scope

M652 remains frozen-head only:

```text
freeze BC5660 actor/recurrent/critic/log_std
train only SequenceDeltaHead
write no actor checkpoint
run no PPO
promote nothing
```

The actor input contract remains unchanged. Source ids, target labels, split
labels, candidate ids, and margin metadata remain objective metadata only.

## Rows

Use M641/M649 corpus metadata.

Normal target rows:

```text
all train rows
```

Wrong-history contrast rows:

```text
variant == wrong_matched_history
```

In the current split:

```text
train wrong-history source: 30
source-heldout wrong-history source: 32
```

Delayed-history rows are not forced to be wrong-history rows in M652. They are
reported separately but not used in the rejection loss.

## Loss

Let:

```text
delta_star = target_action_sequence - normal_base_action_sequence
z_n = frozen_features(observation, normal_hidden)
z_w = frozen_features(observation, wrong_history_hidden)
p_n = head(z_n)
p_w = head(z_w)
d_n = masked_mse(p_n, delta_star)
d_w = masked_mse(p_w, delta_star)
```

Primary normal target loss:

```text
L_normal = source_balanced_mean(d_n over train rows)
```

Wrong-history rejection loss:

```text
L_wrong_margin = mean_wrong_rows softplus(margin_mse + d_n - d_w)
```

This requires wrong-history prediction to be farther from the normal corrective
target than the normal-history prediction.

Optional weak wrong-history zero-delta anchor:

```text
L_wrong_zero = mean_wrong_rows masked_mse(p_w, 0)
```

Use a small coefficient only:

```text
wrong_zero_coef <= 0.10
```

Reason: we know wrong history should not predict the same correction, but we do
not yet know the perfect rejected sequence. Zero-delta is only a conservative
anchor around current base behavior.

Combined loss:

```text
L = L_normal
  + contrast_coef * L_wrong_margin
  + wrong_zero_coef * L_wrong_zero
```

M652 default:

```text
contrast_coef: 1.0
wrong_zero_coef: 0.05
margin_mse: 0.00025
```

## Repeat Protocol

M652 should run three seeds:

```text
6510
6511
6512
```

Training:

```text
epochs: 240
learning_rate: 0.001
weight_decay: 0.0001
hidden_dim: 64
best-validation selection: source-heldout normal loss with wrong-history gap tiebreak
```

Best validation selection:

```text
primary: minimize source_holdout_validation normal_delta_mse
tiebreak: maximize wrong_history_gap_mse on source-heldout wrong rows
```

## Metrics

M652 must report:

```text
normal_train_delta_mse
normal_validation_delta_mse
wrong_train_normal_mse
wrong_train_variant_mse
wrong_train_gap_mse = variant - normal
wrong_validation_normal_mse
wrong_validation_variant_mse
wrong_validation_gap_mse = variant - normal
wrong_train_prediction_gap_l2
wrong_validation_prediction_gap_l2
actor_checksum_before
actor_checksum_after
```

Also report delayed-history rows separately.

## Pass Criteria

At least `2/3` seeds must satisfy:

```text
actor checksum unchanged
best head written
no actor checkpoint written
normal_validation_delta_mse <= 0.0010
wrong_train_gap_mse >= 0.00025
wrong_validation_gap_mse >= 0.00010
wrong_train_prediction_gap_l2 >= 0.01
wrong_validation_prediction_gap_l2 >= 0.005
```

The normal validation threshold is looser than M649 because M652 adds a
contrast constraint. It must preserve useful correction learning while creating
wrong-history separation.

## Interpretation Rules

If M652 passes:

```text
head-only normal correction learning and wrong-history separation both exist;
audit before adapter design.
```

If normal loss passes but wrong-history gap fails:

```text
the current frozen features may not contain enough wrong-history information;
design a feature/contrast audit rather than actor coupling.
```

If wrong-history gap passes but normal loss regresses:

```text
the contrast objective is too strong; tune objective design, not actor coupling.
```

## Decision

`bc_v2_wrong_history_contrast_design_admit_m652`

## Next

`m652-bc-v2-wrong-history-contrast-implementation`
