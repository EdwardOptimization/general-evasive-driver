# M931 V4 Public Base Policy-Head No-Tail-Lift Audit

## Purpose

M930 updated only `model.actor_mean` from the M399 public base and preserved
all non-head checksums. The result was clean but negative:

```text
candidate_alpha_count: 0
result_class: public_base_policy_head_trust_region_probe_no_tail_lift
```

M931 audits what this means before any broader actor update is designed. This
milestone is audit-only: no training, replay, PPO, private holdout, or
promotion.

## Evidence Reviewed

- M930 summary:
  `runs/m930_v4_public_base_policy_head_trust_region_probe/summary.json`
- M930 alpha metrics:
  `runs/m930_v4_public_base_policy_head_trust_region_probe/alpha_metrics.csv`
- M930 training metrics:
  `runs/m930_v4_public_base_policy_head_trust_region_probe/training_metrics.csv`
- M930 raw actor-mean checkpoint:
  `runs/m930_v4_public_base_policy_head_trust_region_probe/checkpoints/raw_actor_mean_update.pt`

## M930 Facts

The run was internally valid:

```text
positive_rows: 1213
reconstructed_rows: 1213
joined_target_rows: 122
training_started: true
actor_mean_changed: true
feature_backbone_changed: false
critic_changed: false
log_std_changed: false
non_actor_mean_changed: false
replay_used: false
ppo_used: false
promoted: false
```

The registered alphas were intentionally small:

```text
0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100
```

All registered alphas passed normal retention. None passed tail lift or target
loss. At the largest registered alpha:

```text
alpha: 0.100
normal_retention_pass: true
tail_lift_pass: false
target_loss_pass: false
normal_intervention_gap_p10: 0.0069598248
base near_gap_p10:           0.0069862247
gap_deficit_mean:            0.0169138894
base gap_deficit_mean:       0.0168765560
low_tail_fraction:           0.4105523527
base low_tail_fraction:      0.4105523495
```

Training loss did move the raw policy-head direction, but the registered alpha
window is too small to decide whether the direction is globally useless or only
too weak inside the current trust region. The final epoch has:

```text
loss: 0.0011316928
target_loss: 0.0005621008
low_tail_gap_floor_loss: 0.0001934265
low_tail_deficit_loss: 0.0004072453
normal_retention_loss: 0.0000062455
intervention_anchor_loss: 0.0000065796
gap_mean: 0.1446675956
```

## Classification

M930 should not yet be classified as proof that actor-head updates cannot help.
It proves a narrower claim:

```text
actor_mean-only training produced no admissible tail-lift candidate inside the
pre-registered conservative interpolation window.
```

This is different from M927:

- M927 found tail-lift directions from residual heads, but the tail-lift
  directions violated normal retention.
- M930 found normal-retained policy-head movement, but no tail-lift movement in
  the registered alpha window.

The missing distinction is whether M930 raw actor-head direction produces tail
lift at larger alphas. Without that, a broader actor update could be premature:
it might be fixing leverage that the current actor-head direction already has
outside the small window, or it might be chasing an objective that does not
create the right low-tail gap at all.

## Decision

Do not broaden the trainable actor surface yet.

Route first to a no-training extended-alpha audit of the already saved M930 raw
actor-head direction:

```text
m932-v4-public-base-policy-head-raw-direction-feasibility-audit
```

M932 should evaluate the M930 raw actor-head update across a wider alpha grid,
for example:

```text
0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100,
0.200, 0.350, 0.500, 0.750, 1.000
```

using the same M912/M919 objective metrics and no additional training.

## Route Logic

If M932 finds tail lift only outside normal retention:

```text
classification: policy_head_trust_region_conflict
next route: controlled broader surface design, likely final fusion + actor_mean
```

If M932 finds no tail lift even at raw alpha:

```text
classification: policy_head_leverage_insufficient_or_objective_mismatch
next route: audit target/low-tail active set before broader actor update
```

If M932 finds an admissible alpha:

```text
classification: policy_head_candidate
next route: exact no-update compatibility design before replay
```

Replay, PPO, and promotion remain blocked until an objective candidate exists
and passes the appropriate exact-first checks.
