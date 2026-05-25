# M930 V4 Public Base Policy-Head Trust-Region Probe Implementation

## Purpose

M929 routed away from residual-head bridge variants after M927 showed a
trust-region conflict. M930 tests the smallest policy-level update that could
still be compatible with the public-base proof path:

```text
update only model.actor_mean
freeze feature/recurrent encoders, critic, log_std, and actor inputs
evaluate objective gates before replay, PPO, or promotion
```

This is an objective-only probe. It does not run exact compatibility, replay,
PPO, private holdout, or promotion.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_policy_head_trust_region_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m930_v4_public_base_policy_head_trust_region_probe \
  --device cpu \
  --epochs 40 \
  --seed 9300
```

## Artifacts

- Summary: `runs/m930_v4_public_base_policy_head_trust_region_probe/summary.json`
- Alpha metrics: `runs/m930_v4_public_base_policy_head_trust_region_probe/alpha_metrics.csv`
- Objective rows: `runs/m930_v4_public_base_policy_head_trust_region_probe/objective_rows.csv`
- Training metrics: `runs/m930_v4_public_base_policy_head_trust_region_probe/training_metrics.csv`
- Raw actor-mean checkpoint: `runs/m930_v4_public_base_policy_head_trust_region_probe/checkpoints/raw_actor_mean_update.pt`

## Result

M930 is a clean negative.

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
target_rows_count: 122
joined_target_rows: 122
strict_target_rows: 103
near_tail_target_rows: 19
low_tail_rows_count: 498
missing_target_keys: 0
training_started: true
actor_mean_changed: true
feature_backbone_changed: false
critic_changed: false
log_std_changed: false
non_actor_mean_changed: false
candidate_alpha_count: 0
result_class: public_base_policy_head_trust_region_probe_no_tail_lift
```

No actor-input contract change occurred. The only changed parameter group is
`actor_mean`.

## Alpha Gate Summary

The registered interpolation alphas all pass normal retention, but none pass
tail lift or target loss:

```text
alpha   normal_retention  tail_lift  target_loss  low_tail_fraction  gap_p10
0.001   true              false      false        0.412201           0.006907
0.002   true              false      false        0.412201           0.006908
0.005   true              false      false        0.412201           0.006909
0.010   true              false      false        0.412201           0.006912
0.020   true              false      false        0.412201           0.006917
0.050   true              false      false        0.410552           0.006933
0.100   true              false      false        0.410552           0.006960
```

The best normal-retaining row is alpha `0.100`, but it still fails:

```text
normal_intervention_gap_p10: 0.0069598248
base near_gap_p10:           0.0069862247
gap_deficit_mean:            0.0169138894
base gap_deficit_mean:       0.0168765560
low_tail_fraction:           0.4105523527
base low_tail_fraction:      0.4105523495
target_action_mse_mean:      0.0005329171
baseline target MSE:         0.0005333332
strict target MSE:           0.0005333830
```

The total target MSE moves slightly in the intended direction at larger alpha,
but the strict target subset does not improve and the low-tail evidence does
not move. There is no hidden candidate checkpoint to admit into exact or replay
work.

## Interpretation

This is not a reconstruction failure, target-join failure, contract violation,
or optimizer-routing failure. The actor-mean-only surface is simply too local
for the current M399 public-base low-tail objective: it can preserve normal
actions, but it does not increase the normal/intervention gap or reduce the
low-tail deficit.

This differs from M927:

- M927 found tail-lift directions from residual heads, but only outside normal
  retention.
- M930 keeps normal retention, but finds no tail-lift direction from
  actor_mean-only training.

Together, they suggest the next audit should decide whether the policy-level
trust-region branch needs a broader but still controlled update surface, such
as actor_mean plus the final fusion layer, or whether the current objective is
not the right active set for M399.

## Decision

Do not run replay, PPO, or promotion from M930.

Next blocker:

```text
m931-v4-public-base-policy-head-no-tail-lift-audit
```

M931 should audit whether the failure is best classified as actor-head leverage
insufficiency, objective active-set mismatch, or another public-base
trust-region stop condition before any broader actor update is designed.
