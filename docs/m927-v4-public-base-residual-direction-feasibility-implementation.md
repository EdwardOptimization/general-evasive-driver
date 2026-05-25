# M927 V4 Public-Base Residual Direction Feasibility Implementation

## Purpose

M927 implements and runs the M926 no-training feasibility audit.

Allowed:

```text
load existing M921 and M924 residual heads
evaluate deterministic direction mixtures and alphas
write feasibility artifacts
```

Forbidden:

```text
train or fit a residual head
update M399 actor backbone
change actor inputs
run M880 exact compatibility
run replay
run PPO
promote a checkpoint
```

## Implementation

M927 adds:

```text
src/autodrift/public_base_residual_direction_feasibility.py
tests/test_public_base_residual_direction_feasibility.py
```

The sweep evaluates:

```text
direction_mix = (1 - w) * residual_M921 + w * residual_M924

w:
  0.00, 0.10, 0.20, ..., 1.00

alpha:
  0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35,
  0.50, 0.75, 1.00
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_residual_direction_feasibility \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --m921-residual-head runs/m921_v4_public_base_regenerated_target_residual_probe/residual_head.pt \
  --m924-residual-head runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/residual_head.pt \
  --run-dir runs/m927_v4_public_base_residual_direction_feasibility \
  --device cpu
```

## Result

Summary:

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
target_rows_count: 122
joined_target_rows: 122
missing_target_keys: 0
low_tail_rows_count: 498
feature_dim: 128
grid_rows: 121
feasible_candidate_count: 0
tail_lift_rows: 22
normal_retained_tail_lift_rows: 0
actor_backbone_changed: false
training_started: false
residual_head_fit_started: false
m880_exact_used: false
replay_used: false
ppo_used: false
promoted: false
result_class: public_base_residual_direction_feasibility_trust_region_conflict
```

M927 fails to find any feasible mixture:

```text
feasible_candidate_count: 0
```

The negative result is clean:

```text
reconstructed_rows: 1213 / 1213
joined_target_rows: 122 / 122
training_started: false
actor_backbone_changed: false
```

## Boundary Rows

Best normal-retaining low-tail row:

```text
mix_weight_m924: 0.1
alpha: 0.3
normal_retention_pass: true
target_loss_pass: true
tail_lift_pass: false
low_tail_fraction: 0.39241549372673035
gap_deficit_mean: 0.015864063668550782
normal_intervention_gap_p10: 0.007841135375201702
first_action_drift_from_base_mean: 0.0029116761565967774
```

Best tail-lift row:

```text
mix_weight_m924: 1.0
alpha: 1.0
normal_retention_pass: false
target_loss_pass: false
tail_lift_pass: true
low_tail_fraction: 0.16652926802635193
gap_deficit_mean: 0.0076176024472797005
normal_intervention_gap_p10: 0.016931863501667976
first_action_drift_from_base_mean: 0.05324622001022911
```

Lowest-drift tail-lift row:

```text
mix_weight_m924: 0.2
alpha: 1.0
normal_retention_pass: false
target_loss_pass: true
tail_lift_pass: true
low_tail_fraction: 0.2984336316585541
gap_deficit_mean: 0.012804917679440848
first_action_drift_from_base_mean: 0.013699799856694641
```

There is no row where tail lift survives inside the normal-retention envelope.

## Interpretation

M927 supports that the current residual-head bridge is infeasible under the
registered gates, at least for mixtures of the two learned directions:

```text
M921 direction: target-aligned, normal-retaining, weak low-tail lift
M924 direction: low-tail-aligned, non-retaining, target-conflicting
mixtures: no overlap between tail_lift_pass and normal_retention_pass
```

The active blocker is no longer target generation or residual training
plumbing. It is a trust-region conflict in the residual-head bridge.

## Decision

Decision:

```text
public_base_residual_direction_feasibility_trust_region_conflict_route_to_policy_level_strategy_audit
```

Next:

```text
m928-v4-public-base-trust-region-feasibility-audit
```

M928 should decide whether to:

```text
1. audit the normal-retention envelope further;
2. move to a policy-level trust-region actor-update design;
3. return to corpus/source strategy instead of residual-head bridge training.
```

## Supported Claims

M927 supports:

```text
1. Existing M921/M924 residual directions do not contain an alpha/mix candidate
   that satisfies all objective gates.
2. Tail-lift rows exist, but all violate normal retention.
3. Normal-retaining rows exist, but none produce enough tail lift.
4. No training, exact compatibility, replay, PPO, or promotion occurred.
```

## Unsupported Claims

M927 does not support:

```text
exact compatibility;
replay retention;
PPO safety;
driver improvement;
checkpoint promotion;
universal infeasibility of every possible future actor update.
```
