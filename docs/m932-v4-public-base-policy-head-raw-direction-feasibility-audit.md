# M932 V4 Public Base Policy-Head Raw Direction Feasibility Audit

## Purpose

M931 concluded that M930's negative result only covered the conservative alpha
window up to `0.100`. M932 performs a no-training audit of the already saved
M930 raw actor_mean direction across an extended alpha grid.

This milestone does not train, run exact compatibility, run replay, run PPO, or
promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_policy_head_raw_direction_feasibility \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m930_v4_public_base_policy_head_trust_region_probe/checkpoints/raw_actor_mean_update.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m932_v4_public_base_policy_head_raw_direction_feasibility \
  --device cpu \
  --alphas 0.001,0.002,0.005,0.010,0.020,0.050,0.100,0.200,0.350,0.500,0.750,1.000
```

## Artifacts

- Summary: `runs/m932_v4_public_base_policy_head_raw_direction_feasibility/summary.json`
- Alpha metrics: `runs/m932_v4_public_base_policy_head_raw_direction_feasibility/alpha_metrics.csv`
- Objective rows: `runs/m932_v4_public_base_policy_head_raw_direction_feasibility/objective_rows.csv`

## Result

M932 is a clean no-training negative with weak positive low-tail movement.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
training_started: false
actor_mean_changed_between_checkpoints: true
feature_backbone_changed_between_checkpoints: false
critic_changed_between_checkpoints: false
log_std_changed_between_checkpoints: false
non_actor_mean_changed_between_checkpoints: false
candidate_alpha_count: 0
tail_lift_rows: 0
normal_retained_tail_lift_rows: 0
result_class: public_base_policy_head_raw_direction_feasibility_no_tail_lift
```

The raw checkpoint differs from M399 only in `actor_mean`, so the audit is not a
contract artifact.

## Alpha Summary

All evaluated alphas, including raw alpha `1.0`, pass normal retention. None
pass the registered tail-lift gate.

At alpha `1.0`:

```text
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: false
first_action_drift_from_base_mean: 0.0023831567
first_action_drift_from_base_p95:  0.0040617720
normal_anchor_mse_mean:            0.0000022419
normal_anchor_mse_p95:             0.0000054996
normal_intervention_gap_p10:       0.0074899575
base near_gap_p10:                 0.0069862247
gap_deficit_mean:                  0.0163790291
base gap_deficit_mean:             0.0168765560
low_tail_fraction:                 0.3973619044
base low_tail_fraction:            0.4105523495
target_action_mse_mean:            0.0005316580
baseline target MSE:               0.0005333332
strict_target_action_mse_mean:     0.0005362949
near_tail_target_action_mse_mean:  0.0005065208
```

So the raw direction is not useless:

- low-tail rows drop from about `498` to `482`;
- low-tail fraction improves by about `0.01319`;
- gap deficit improves by about `0.000498`;
- target MSE improves in aggregate and on near-tail targets.

But it is below the registered tail-lift effect-size threshold:

- p10 gap lift is only about `0.000504`;
- deficit improvement is only about `0.000498`;
- low-tail fraction improvement is not enough;
- strict target MSE worsens slightly.

## Interpretation

M932 rules out the simplest trust-region explanation:

```text
M930 did not fail because the registered alpha window stopped before a strong
raw actor_head direction.
```

It also argues against immediately broadening the trainable surface:

```text
The actor_mean direction remains normal-safe even at raw alpha 1.0 and moves
low-tail metrics in the right direction, but the effect is too weak.
```

The next controlled question is therefore objective pressure and active-set
alignment, not feature-backbone training. In particular, the strict regenerated
target subset is not aligned with the weak low-tail improvement at alpha `1.0`,
while near-tail targets and aggregate target MSE improve. That makes the
target-action gate an active-set issue worth handling explicitly.

## Decision

Do not run replay, PPO, or promotion from M932.

Do not broaden the actor update surface yet.

Next blocker:

```text
m933-v4-public-base-policy-head-low-tail-pressure-design
```

M933 should design a second actor_mean-only objective pass with stronger
low-tail effect-size pressure and explicit target-active-set diagnostics. The
goal is to test whether the existing actor head has enough leverage under a
better low-tail objective before touching feature/recurrent encoders.
