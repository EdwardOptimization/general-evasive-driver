# M936 V4 Public Base Controlled Fusion Surface Design

## Purpose

M935 closed the actor_mean-only branch. M936 designs the next controlled
trainable surface. It is still conservative: keep the recurrent belief encoder
and perception/context encoders frozen, but allow the final fusion layer that
combines hidden response state and scene context to move with the policy head.

M936 is design-only. It does not train, run exact compatibility, run replay, run
PPO, or promote.

## Why Not Continue Actor Mean Only

M930 showed conservative actor_mean-only training has no tail lift.

M932 showed the M930 raw actor_mean direction remains normal-safe through
alpha `1.0`, but still has no tail-lift row.

M934 showed stronger actor_mean-only pressure can create tail lift, but only
after normal retention fails:

```text
alpha 0.2: normal_retention_pass true, tail_lift_pass false
alpha 1.0: normal_retention_pass false, tail_lift_pass true
```

This is enough to stop actor_mean-only coefficient search. The next surface must
increase controllable leverage without touching the recurrent self-ID machinery.

## Allowed Trainable Surface

The first broader surface should be:

```text
actor_mean.weight
actor_mean.bias
response_context_fusion.0.weight
response_context_fusion.0.bias
```

The `response_context_fusion` layer is narrow and mechanism-relevant. It is the
last layer that combines:

```text
next_hidden
context_encoded
next_hidden * context_encoded
```

before the policy head. This is a reasonable next surface because actor_mean
alone may not have enough leverage to reshape the hidden/context interaction,
while unfreezing response/context encoders or GRU would directly alter the
self-ID machinery.

## Forbidden Trainable Surface

M937 must freeze:

```text
response_encoder.*
context_encoder.*
online_gru_cell.*
critic.*
log_std
privileged_encoder.*
privileged_residual.*
sequence_tail.*
response_prediction_head.*
actor inputs / observation contract
```

The P0 human-view no-wheel 72-dim actor input contract remains unchanged.

## Implementation Requirement

The actor_mean-only tools cache final fused features. That is not enough for
fusion-layer training because gradients must pass through
`response_context_fusion`.

M937 must reconstruct trainable samples as:

```text
normal_observation
normal_hidden
intervention_observation
intervention_hidden
base_normal_action
base_intervention_action
target_gap
target_action / source label
```

Then during training:

```text
normal_features = model.recurrent_features_tensor(normal_observation, normal_hidden)[0]
intervention_features = model.recurrent_features_tensor(intervention_observation, intervention_hidden)[0]
normal_action = tanh(model.actor_mean(normal_features))
intervention_action = tanh(model.actor_mean(intervention_features))
```

Only the allowed surface should require gradients.

## Objective

Start with the M934 stronger low-tail pressure, because it demonstrated the
right low-tail direction:

```text
target_action_coef:          0.10
low_tail_gap_floor_coef:    10.00
low_tail_deficit_coef:       6.00
normal_retention_coef:      12.00
intervention_anchor_coef:    0.50
parameter_anchor_coef:       0.001
epochs:                    80
lr:                         0.0005
```

Use a lower learning rate than M934 because the trainable surface is broader.

## Alpha Grid

Use:

```text
0.001, 0.002, 0.005, 0.010, 0.020, 0.050,
0.100, 0.200, 0.350, 0.500, 0.750, 1.000
```

## Required Checksums

M937 summary must report:

```text
actor_mean_changed
fusion_changed
response_encoder_changed
context_encoder_changed
online_gru_changed
critic_changed
log_std_changed
forbidden_parameter_changed
```

The implementation is a contract artifact if any forbidden group changes.

## Required Diagnostics

M937 must report the same diagnostic classes added in M934:

```text
strict_candidate_count
low_tail_effect_candidate_count
target_tolerance_candidate_count
normal_safe_low_tail_trend_count
```

Only `strict_candidate_count > 0` may route toward exact compatibility design.
Other positive diagnostics require audit first.

## Route Logic

If strict candidate exists:

```text
route: exact no-update compatibility design before replay
```

If low-tail effect candidate exists but target loss fails:

```text
route: target-active-set audit
```

If tail lift exists only outside normal retention:

```text
route: controlled fusion trust-region audit
```

If there is no tail lift and no normal-safe trend:

```text
route: branch audit before touching encoders or GRU
```

## Next Blocker

```text
m937-v4-public-base-controlled-fusion-surface-implementation
```

M937 should implement the observation/hidden sample loader and run the
objective-only controlled fusion surface probe. Replay, PPO, and promotion
remain blocked.
