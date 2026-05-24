# M712 Actor-Head History-Signal Coupling Design

## Purpose

M712 designs the first no-training diagnostic in the new
`actor_head_history_signal_coupling` branch.

M710/M711 established:

```text
wrong-history signal exists in raw hidden and fused feature space
wrong-history signal does not become deployed action or margin change
result_class: action_washout
```

M712 asks a narrower question:

```text
why does the actor head ignore the fused wrong-history feature direction?
```

This milestone is design-only:

```text
no implementation
no actor update
no optimizer
no PPO
no checkpoint promotion
no actor-input change
```

## Diagnostic Decomposition

M713 should reconstruct M710-style cross-fault pairs and compute these feature
objects for each preferred observation:

```text
f_normal = recurrent_features_tensor(obs, h_normal).features
f_wrong  = recurrent_features_tensor(obs, h_wrong).features
f_reset  = recurrent_features_tensor(obs, h_zero).features

z_normal = actor_mean(f_normal)
z_wrong  = actor_mean(f_wrong)
z_reset  = actor_mean(f_reset)

a_normal = tanh(z_normal)
a_wrong  = tanh(z_wrong)
a_reset  = tanh(z_reset)
```

Then decompose:

```text
feature_delta_l2:
  ||f_variant - f_normal||

pre_tanh_delta_l2:
  ||z_variant - z_normal||

action_delta_l2:
  ||a_variant - a_normal||

projection_ratio:
  pre_tanh_delta_l2 / feature_delta_l2

tanh_attenuation_ratio:
  action_delta_l2 / pre_tanh_delta_l2

feature_to_action_ratio:
  action_delta_l2 / feature_delta_l2
```

Compare:

```text
normal_vs_wrong_history
normal_vs_reset_hidden
```

The comparison is important. M710 already showed reset-hidden reaches action
while wrong-history mostly does not. M713 should determine whether that is
because wrong-history feature deltas are smaller, point in actor-head
null-space directions, or get attenuated by tanh saturation.

## Feature-Delta Amplification Line Search

M713 should also run a counterfactual feature-only line search:

```text
f_alpha = f_normal + alpha * (f_variant - f_normal)
a_alpha = tanh(actor_mean(f_alpha))
```

Evaluate alphas:

```text
0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0
```

Record:

```text
alpha_to_action_threshold:
  smallest alpha where ||a_alpha - a_normal|| >= 0.015

action_l2_at_alpha_2
action_l2_at_alpha_4
action_l2_at_alpha_8
action_l2_at_alpha_16
```

These amplified actions are diagnostic counterfactuals only. They are not
deployed actor behavior and must not be treated as a policy improvement.

## Required Artifact Rows

M713 should write one row per pair and variant:

```text
pair_id
variant
seed
step
fault_family_pair
severity_pair
sentinel_pair
assigned_split
feature_delta_l2
pre_tanh_delta_l2
action_delta_l2
projection_ratio
tanh_attenuation_ratio
feature_to_action_ratio
alpha_to_action_threshold
action_l2_at_alpha_2
action_l2_at_alpha_4
action_l2_at_alpha_8
action_l2_at_alpha_16
normal_margin
variant_margin
margin_gap
success_drop
```

Write grouped summaries:

```text
variant_summary.csv
fault_family_pair_variant_summary.csv
sentinel_summary.csv
alpha_summary.csv
```

## Result Classes

M713 should classify:

```text
feature_delta_too_small:
  wrong feature deltas are much smaller than reset deltas and require large
  amplification before action threshold.

actor_head_projection_washout:
  wrong feature deltas are nontrivial but pre-tanh projection ratio is much
  weaker than reset.

tanh_saturation_washout:
  pre-tanh deltas are nontrivial but action/pre-tanh attenuation is much weaker
  than reset.

near_threshold_action_washout:
  many wrong rows approach threshold under alpha <= 2 or alpha <= 4, suggesting
  an objective may recover action coupling.

amplification_not_action_relevant:
  even alpha 16 rarely crosses action threshold.

actor_head_coupling_positive:
  wrong feature directions reach action threshold at low alpha for enough
  source-diverse rows, admitting an objective-design audit.
```

## Pre-Registered Thresholds

Use these as diagnostics:

```text
min_action_l2: 0.015
low_alpha_limit: 4.0
high_alpha_limit: 16.0
min_low_alpha_rows: 30
min_unique_fault_pairs: 4
projection_ratio_reset_fraction: 0.50
tanh_attenuation_reset_fraction: 0.50
```

Interpretation rules:

```text
actor_head_coupling_positive:
  wrong rows with alpha_to_action_threshold <= 4.0 >= 30
  and unique fault pairs among those rows >= 4

amplification_not_action_relevant:
  wrong rows with alpha_to_action_threshold <= 16.0 < 30

actor_head_projection_washout:
  wrong projection_ratio mean < 50% of reset projection_ratio mean

tanh_saturation_washout:
  wrong tanh_attenuation mean < 50% of reset tanh_attenuation mean
```

The thresholds should not be relaxed after seeing results.

## Command Design

M713 should implement:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.actor_head_history_signal_coupling_audit \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/cross_fault_hidden_condition_scenarios.json \
  --seed-start 41000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m713_actor_head_history_signal_coupling
```

It can reuse the M710 collection and matching code, but it should not rerun
closed-loop continuations unless needed for margin columns. If it reuses M710's
replay path, it must keep the no-training/no-PPO contract.

## Required M713 Artifacts

```text
runs/m713_actor_head_history_signal_coupling/summary.json
runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv
runs/m713_actor_head_history_signal_coupling/variant_summary.csv
runs/m713_actor_head_history_signal_coupling/fault_family_pair_variant_summary.csv
runs/m713_actor_head_history_signal_coupling/sentinel_summary.csv
runs/m713_actor_head_history_signal_coupling/alpha_summary.csv
docs/m713-actor-head-history-signal-coupling-implementation.md
```

## Decision

M712 admits:

```text
m713-actor-head-history-signal-coupling-implementation
```

M712 does not admit:

```text
actor update
PPO
checkpoint promotion
source export
actor input changes
```
