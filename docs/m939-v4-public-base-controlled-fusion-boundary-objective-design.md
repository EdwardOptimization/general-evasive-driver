# M939 V4 Public Base Controlled Fusion Boundary Objective Design

## Purpose

M938 showed that the M937 controlled-fusion raw direction has a normal-retained
near miss around alpha `0.15`. M939 designs an interpolation-aware objective
that trains directly for this boundary instead of widening the trainable surface
or running PPO.

M939 is design-only. It does not train, run exact compatibility, run replay, run
PPO, or promote.

## M938 Boundary Evidence

Alpha `0.15`:

```text
normal_retention_pass: true
tail_lift_pass: false
first_action_drift_from_base_mean: 0.0023812945
first_action_drift_from_base_p95:  0.0062792329
normal_anchor_mse_mean:            0.0000031994
normal_anchor_mse_p95:             0.0000131429
normal_intervention_gap_p10:       0.0093974071
gap_deficit_mean:                  0.0150613526
low_tail_fraction:                 0.3858202696
```

Alpha `0.25`:

```text
normal_retention_pass: false
tail_lift_pass: true
gap_deficit_mean: 0.0138036459
low_tail_fraction: 0.3569661975
```

The gap is narrow and specific:

```text
normal retention is still OK near 0.15;
tail-lift p10 and low-tail fraction are close enough at 0.15;
gap-deficit mean is the main remaining miss;
tail lift starts only after normal retention has already failed.
```

## Trainable Surface

Keep the M936/M937 surface unchanged:

```text
allowed:
  actor_mean.weight
  actor_mean.bias
  response_context_fusion.0.weight
  response_context_fusion.0.bias

forbidden:
  response_encoder.*
  context_encoder.*
  online_gru_cell.*
  critic.*
  log_std
  actor inputs
```

No encoder or GRU update is allowed in this branch without a new synthesis.

## Boundary-Aware Objective

M940 should optimize the raw controlled-fusion update, but compute the training
loss through differentiable interpolation at the boundary alphas:

```text
train_alphas:
  0.125, 0.150, 0.175
```

For each train alpha, use effective allowed parameters:

```text
theta_eff = theta_base + alpha * (theta_raw - theta_base)
```

Only the allowed linear layers need differentiable interpolation:

```text
response_context_fusion.0
actor_mean
```

The frozen response encoder, context encoder, and GRU still compute:

```text
response_encoded
context_encoded
next_hidden
fusion_input = [next_hidden, context_encoded, next_hidden * context_encoded]
```

Then M940 should apply the interpolated fusion linear layer, tanh, interpolated
actor_mean, and final tanh action.

## Loss Terms

Use the same reconstructed observation/hidden samples as M937.

Recommended loss:

```text
loss =
  12.0 * boundary_deficit_loss
+  10.0 * boundary_gap_floor_loss
+  10.0 * normal_retention_hinge
+  2.0  * normal_anchor_mse
+  0.5  * intervention_anchor_mse
+  0.05 * target_action_loss
+  0.001 * allowed_parameter_anchor
```

Definitions:

```text
boundary_deficit_loss:
  low-tail rows only;
  relu(gap_deficit - 0.01475)^2

boundary_gap_floor_loss:
  low-tail rows only;
  relu(0.00950 - normal_intervention_gap)^2

normal_retention_hinge:
  all rows;
  relu(first_action_drift - 0.00280)^2
  + relu(row_action_mse - 0.00000350)^2

normal_anchor_mse:
  all rows;
  mean squared action difference from M399 base normal action

intervention_anchor_mse:
  all rows;
  mean squared action difference from M399 base intervention action

target_action_loss:
  target rows;
  weighted M919 target action MSE, auxiliary only
```

Rationale:

- The deficit target `0.01475` is just beyond the M938 alpha `0.15` near miss
  and slightly inside the registered deficit requirement.
- The gap floor `0.00950` is near the alpha `0.15` p10 value and keeps the
  p10 component from regressing while deficit is improved.
- Normal retention hinge is explicit because M938 shows normal retention fails
  shortly after the near-miss region.
- Target loss is auxiliary because M938 target MSE worsens at normal-retained
  alphas while the low-tail geometry improves.

## Evaluation Alphas

M940 should evaluate:

```text
0.050, 0.075, 0.100, 0.125, 0.150, 0.175,
0.200, 0.225, 0.250, 0.275, 0.300, 0.325,
0.350, 0.500, 0.750, 1.000
```

## Required Diagnostics

M940 must report:

```text
strict_candidate_count
low_tail_effect_candidate_count
target_tolerance_candidate_count
normal_safe_low_tail_trend_count
boundary_near_miss_count
forbidden_parameter_changed
```

`boundary_near_miss_count` should count normal-retained rows with:

```text
normal_intervention_gap_p10 >= near_base_gap_p10 + P10_LIFT_TARGET
low_tail_fraction <= near_base_low_tail_fraction - LOW_TAIL_FRACTION_LIFT_TARGET
gap_deficit_mean <= near_base_gap_deficit_mean - 0.0015
```

Only strict candidates can route toward exact compatibility. Near-miss counts
are diagnostic.

## Route Logic

If strict candidate exists:

```text
route: exact no-update compatibility design
```

If low-tail effect candidate exists but target loss fails:

```text
route: target-active-set audit
```

If only boundary near-miss improves:

```text
route: controlled fusion boundary audit; do not widen surface yet
```

If normal retention fails at all useful alphas:

```text
route: controlled fusion trust-region synthesis before touching encoders/GRU
```

## Next Blocker

```text
m940-v4-public-base-controlled-fusion-boundary-objective-implementation
```

M940 should implement the differentiable interpolation objective and run one
small objective-only probe. Replay, PPO, and promotion remain blocked.
