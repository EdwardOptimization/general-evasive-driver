# M657 Wrong-History Fusion-Boundary Probe Design

## Purpose

M657 designs a frozen feature-view comparison probe after M655/M656 localized
the current blocker to the response/context fusion boundary.

This milestone is design-only:

```text
no actor update
no PPO
no checkpoint promotion
```

M658 may train diagnostic auxiliary heads, but all BC5660 actor, recurrent,
critic, and log-std parameters must remain frozen.

## Blocker From M656

M656 concluded:

```text
wrong-history information exists in recurrent state,
survives the current-response GRU update,
but is weak at the fused actor feature and actor-action boundary.
```

The key M655 numbers were:

```text
wrong raw_hidden_l2:                  0.097340
wrong next_hidden_retention_ratio:    0.409547
wrong fused_feature_l2:               0.014905
wrong actor_tanh_action_l2:           0.000685
wrong_to_delayed_feature_l2_ratio:    0.202695
wrong_to_delayed_action_l2_ratio:     0.051232
```

So M658 should not ask "can fused features learn a generic sequence
correction?" That was already positive in M649 and negative for wrong-history
separation in M652. It should ask:

```text
Is wrong-history separation learnable from a pre-fusion view?
```

## Feature Views

M658 should compute three frozen feature views for the same corpus rows:

```text
fused:
  model.recurrent_features_tensor(...).features
  This reproduces the M649-M652 boundary.

next_hidden:
  model.recurrent_features_tensor(...).next_hidden
  This exposes the post-current-response recurrent belief before fusion.

fused_plus_next_hidden:
  concat(fused, next_hidden)
  This tests whether adding the belief state to the existing actor feature
  gives the auxiliary head enough separability without removing scene context.
```

For each row, compute each view under:

```text
normal_hidden
variant_hidden
```

using the same current observation.

## Objective

Use the M652 frozen-head wrong-history contrast structure independently for
each view:

```text
delta_star = target_action_sequence - normal_base_action_sequence
z_n = view(observation, normal_hidden)
z_w = view(observation, variant_hidden)
p_n = head_view(z_n)
p_w = head_view(z_w)
d_n = masked_mse(p_n, delta_star)
d_w = masked_mse(p_w, delta_star)

L_normal = source_balanced_mean(d_n over train rows)
L_wrong_margin = mean_wrong_rows softplus(margin_mse + d_n - d_w)
L_wrong_zero = mean_wrong_rows masked_mse(p_w, 0)

L = L_normal
  + contrast_coef * L_wrong_margin
  + wrong_zero_coef * L_wrong_zero
```

Default settings:

```text
seeds: 6570, 6571, 6572
epochs: 240
learning_rate: 0.001
weight_decay: 0.0001
hidden_dim: 64
contrast_coef: 1.0
wrong_zero_coef: 0.05
margin_mse: 0.00025
best validation primary: source-heldout normal_delta_mse
best validation tiebreak: source-heldout wrong_history_gap_mse
```

## Required Metrics

M658 should report per seed and per feature view:

```text
normal_train_delta_mse
normal_validation_delta_mse
wrong_train_normal_mse
wrong_train_variant_mse
wrong_train_gap_mse
wrong_validation_normal_mse
wrong_validation_variant_mse
wrong_validation_gap_mse
wrong_train_prediction_gap_l2
wrong_validation_prediction_gap_l2
normal_validation_improvement
actor_checksum_before
actor_checksum_after
actor_parameters_changed
actor_checkpoint_written
```

It must also report:

```text
source 30 wrong-history train rows
source 32 wrong-history source-heldout rows
delayed-history rows separately
view_feature_dim
view_name
```

## Comparison Rule

M658 should compare every view against the fused view from the same run, not
only against historical M652. This controls for seed, implementation, and
training details.

The important relation is:

```text
next_hidden or fused_plus_next_hidden wrong-history gap
  >
fused wrong-history gap
```

Historical M652 remains context:

```text
M652 wrong_validation_prediction_gap_l2:
  0.000624 - 0.000748
```

## Diagnostic Pass Criteria

M658 is still not a promotion milestone. It passes as a diagnostic if:

```text
actor checksum unchanged for all seeds/views
no actor checkpoint written
fused view reproduced as a weak baseline
at least one of next_hidden or fused_plus_next_hidden has 2/3 seeds with:
  normal_validation_delta_mse <= 0.0010
  wrong_validation_gap_mse >= 0.00010
  wrong_validation_prediction_gap_l2 >= 0.005
  wrong_validation_prediction_gap_l2 >= 3x same-seed fused view
source 30 and source 32 summaries are written
```

If `next_hidden` passes but `fused` fails:

```text
pre-fusion belief state contains useful wrong-history information;
the next design target is the fusion boundary.
```

If `fused_plus_next_hidden` passes but `next_hidden` alone is weak:

```text
the belief signal needs scene/context fusion, but the current fusion loses it;
the next design target is a feature objective or residual adapter.
```

If all views fail:

```text
the M641 wrong-history rows may be too weak or the objective is wrong;
refresh corpus or redesign the preference target before actor coupling.
```

## Required Artifacts

M658 should write:

```text
runs/m658_wrong_history_fusion_boundary_probe/summary.json
runs/m658_wrong_history_fusion_boundary_probe/seed_view_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/view_metrics.csv
runs/m658_wrong_history_fusion_boundary_probe/view_source_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/view_history_variant_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/seed_*/view_*/sequence_delta_head_best_validation.pt
docs/m658-wrong-history-fusion-boundary-probe-implementation.md
```

The head checkpoints are diagnostic auxiliary heads only. No actor checkpoint
may be written.

## Forbidden Shortcuts

Do not:

- update actor/recurrent/critic/log-std parameters;
- run PPO;
- promote any checkpoint;
- use source, split, target, or variant metadata as actor/head input;
- claim closed-loop self-ID proof from an auxiliary head result;
- skip the fused-view baseline.

## Decision

`wrong_history_fusion_boundary_probe_design_admit_m658`

## Next

`m658-wrong-history-fusion-boundary-probe-implementation`
