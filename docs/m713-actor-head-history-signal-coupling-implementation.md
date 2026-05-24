# M713 Actor-Head History-Signal Coupling Implementation

## Purpose

M713 implements the M712 no-training actor-head coupling audit.

M710 showed `action_washout`: wrong-history signal reached fused features but
not deployed actions. M713 asks whether those fused feature directions can
affect actions if amplified along the same direction.

This milestone is diagnostic-only:

```text
no actor update
no optimizer
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M713 adds:

```text
src/autodrift/actor_head_history_signal_coupling_audit.py
tests/test_actor_head_history_signal_coupling_audit.py
```

The runner reconstructs M710-style cross-fault pairs and computes:

```text
feature_delta_l2
pre_tanh_delta_l2
action_delta_l2
projection_ratio
tanh_attenuation_ratio
feature_to_action_ratio
alpha_to_action_threshold
```

It also performs a feature-only counterfactual line search:

```text
f_alpha = f_normal + alpha * (f_variant - f_normal)
a_alpha = tanh(actor_mean(f_alpha))
```

The amplified actions are diagnostic only. They are not deployed actor behavior.

## Command

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

## Artifacts

```text
runs/m713_actor_head_history_signal_coupling/summary.json
runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv
runs/m713_actor_head_history_signal_coupling/variant_summary.csv
runs/m713_actor_head_history_signal_coupling/fault_family_pair_variant_summary.csv
runs/m713_actor_head_history_signal_coupling/sentinel_summary.csv
runs/m713_actor_head_history_signal_coupling/alpha_summary.csv
```

## Result

Summary:

```text
scenario_count:                 9728
snapshot_count:                33026
matched_pair_count:             2048
row_count:                      4096
wrong_rows:                     2048
reset_rows:                     2048
wrong_low_alpha_rows:            164
wrong_high_alpha_rows:          1079
unique_low_alpha_fault_pairs:     20
result_class: actor_head_coupling_positive
actor_head_coupling_positive: true
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Thresholds:

```text
min_action_l2:          0.015
low_alpha_limit:        4.0
high_alpha_limit:       16.0
min_low_alpha_rows:    30
min_unique_fault_pairs: 4
```

M713 passes the diagnostic positive criterion:

```text
wrong_low_alpha_rows:         164 >= 30
unique_low_alpha_fault_pairs:  20 >= 4
```

## Alpha Summary

| Variant | Rows | <=0.5 | <=1 | <=2 | <=4 | <=8 | <=16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| normal_vs_wrong_history | 2048 | 0 | 0 | 67 | 164 | 504 | 1079 |
| normal_vs_reset_hidden | 2048 | 19 | 2014 | 2048 | 2048 | 2048 | 2048 |

Wrong-history directions are much weaker than reset-hidden directions, but they
are not actor-head-null directions. A nontrivial source-diverse subset crosses
the action threshold under alpha <= 4.

## Actor-Head Decomposition

| Variant | Feature Delta Mean | Pre-Tanh Delta Mean | Action Delta Mean | Projection Ratio Mean | Tanh Attenuation Mean | Feature-To-Action Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| normal_vs_wrong_history | 0.015664 | 0.001651 | 0.001587 | 0.096287 | 0.955513 | 0.092014 |
| normal_vs_reset_hidden | 0.099829 | 0.021606 | 0.020228 | 0.215989 | 0.936245 | 0.202227 |

Interpretation:

```text
feature amplitude is smaller for wrong-history than reset-hidden
actor-head projection is weaker for wrong-history than reset-hidden
tanh attenuation is not the primary blocker
```

The tanh layer preserves most of the pre-tanh delta in both variants. The
primary difference is before tanh: wrong-history feature deltas are smaller and
less strongly projected by the actor head.

## Low-Alpha Fault-Pair Coverage

Rows crossing the action threshold at alpha <= 4 cover `20` fault-pair groups.
Top groups:

```text
drive_authority_drop -> drive_authority_drop: 35
drive_authority_drop -> brake_authority_drop: 16
global_mu_drop -> combined_fault:            15
combined_fault -> global_mu_drop:            14
rear_lateral_authority_drop -> combined_fault: 14
rear_lateral_authority_drop -> rear_lateral_authority_drop: 11
combined_fault -> brake_authority_drop:      10
combined_fault -> rear_lateral_authority_drop: 10
```

This is source-diverse enough for an objective-design audit, but it is still a
feature-counterfactual diagnostic, not proof that the current deployed actor
uses wrong-history beliefs.

## Decision

M713 passes as a no-training diagnostic:

```text
artifacts written
alpha line-search positive
actor checksum unchanged
no training, no PPO, no promotion
```

M713 admits an audit before any objective design:

```text
m714-actor-head-history-signal-coupling-audit
```

M713 does not directly admit:

```text
actor update
PPO
checkpoint promotion
deployed self-ID claim
```
