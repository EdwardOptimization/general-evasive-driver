# M921 V4 Public-Base Regenerated-Target Residual Probe Implementation

## Purpose

M921 implements and runs the regenerated-target residual-head probe designed in
M920.

Allowed:

```text
train only a residual head on frozen M399 features
evaluate objective metrics
```

Forbidden:

```text
M399 actor-backbone update
actor-input change
M880 exact compatibility
replay
PPO
checkpoint promotion
```

## Implementation

M921 adds:

```text
src/autodrift/public_base_regenerated_target_residual_probe.py
tests/test_public_base_regenerated_target_residual_probe.py
```

The probe trains a `feature_dim=128` residual head using:

```text
target action loss on M919 accepted target rows
normal-retention anchor over the full reconstructed corpus
low-tail/gap auxiliary losses
```

The M399 actor backbone is frozen and its checksum is checked before and after.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_regenerated_target_residual_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --regenerated-target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --m909-objective-rows runs/m909_v4_public_base_residual_head_probe/objective_rows.csv \
  --run-dir runs/m921_v4_public_base_regenerated_target_residual_probe \
  --device cpu \
  --epochs 40 \
  --seed 9210
```

## Result

Summary:

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
missing_target_keys: 0
regenerated_target_rows_count: 122
joined_target_rows: 122
strict_target_rows: 103
near_tail_target_rows: 19
residual_parameter_count: 8451
epochs: 40
seed: 9210
candidate_alpha_count: 0
actor_backbone_changed: false
training_started: true
residual_only_training: true
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_regenerated_target_probe_no_candidate
```

M921 fails the candidate-alpha gate:

```text
candidate_alpha_count: 0
```

It is not a reconstruction or join failure:

```text
reconstructed_rows: 1213 / 1213
joined_target_rows: 122 / 122
missing_target_keys: 0
actor_backbone_changed: false
```

## Alpha Behavior

The direction is not useless. Target loss improves at every alpha:

```text
baseline_target_action_mse_mean: 0.0005333332
alpha 0.35 target_action_mse_mean: 0.0004932424
alpha 1.00 target_action_mse_mean: 0.0004428685
```

Low-tail metrics also move in the right direction at large alpha:

```text
M912 near_base:
  gap_p10: 0.0069862247
  gap_deficit_mean: 0.016876556
  low_tail_fraction: 0.41055235

alpha 1.00:
  gap_p10: 0.010105353
  gap_deficit_mean: 0.014217697
  low_tail_fraction: 0.37180543
```

But alpha `1.00` fails normal retention:

```text
first_action_drift_from_base_mean: 0.007713428 > 0.003
first_action_drift_from_base_p95: 0.018475107 > 0.008
```

The largest alpha that keeps normal retention in this run is `0.35`, but tail
lift is still too small:

```text
alpha 0.35:
  normal_retention_pass: true
  target_loss_pass: true
  tail_lift_pass: false
  gap_p10: 0.007873416
  gap_deficit_mean: 0.015976072
  low_tail_fraction: 0.39323992
```

## Interpretation

M921 shows that the regenerated target direction is aligned with target-action
loss and weakly aligned with low-tail metrics, but the current objective does
not deliver enough low-tail lift inside the normal-retention trust region.

This is a useful negative result:

```text
target-action imitation alone is not sufficient;
the next objective needs alpha-aware low-tail pressure, likely focused on the
normal-retaining alpha range instead of hoping the residual direction scales.
```

## Decision

Decision:

```text
public_base_regenerated_target_probe_no_candidate_route_to_objective_audit
```

Next:

```text
m922-v4-public-base-regenerated-target-residual-probe-audit
```

## Supported Claims

M921 supports:

```text
1. M919 regenerated targets join cleanly to the full M755 reconstruction corpus.
2. The frozen-M399 residual-head training path is runnable and preserves the
   actor backbone.
3. The current regenerated-target residual objective improves target MSE and
   moves low-tail metrics in the right direction at larger alpha.
4. No alpha satisfies target loss, tail lift, and normal retention together.
```

## Unsupported Claims

M921 does not support:

```text
admitted residual-head alpha;
M880 exact compatibility;
replay retention;
PPO safety;
driver improvement;
checkpoint promotion.
```
