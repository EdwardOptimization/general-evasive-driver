# M818 V4 Adaptive Primary Residual Calibration Audit

## Purpose

M818 audits M817 before allowing a stronger calibration design.

The audit question is:

```text
Did M817 prove a useful adaptive calibrator, or did it only validate the
source-heldout calibration harness and retention gates?
```

M818 is audit-only:

```text
no training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m817_v4_adaptive_primary_residual_calibration/summary.json
runs/m817_v4_adaptive_primary_residual_calibration/gate_summary.csv
runs/m817_v4_adaptive_primary_residual_calibration/training_metrics.csv
runs/m817_v4_adaptive_primary_residual_calibration/train_eval_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/holdout_eval_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/intervention_eval_rows.csv
docs/m817-v4-adaptive-primary-residual-calibration-implementation.md
```

M817 result class:

```text
v4_adaptive_primary_residual_calibration_candidate
```

## Artifact Consistency

M817 wrote the required split, training, exact replay, intervention replay,
gate summary, and documentation artifacts.

The source-heldout split is valid:

```text
split_valid: true
train rows: 57
holdout rows: 28
split units: 55
train unique source groups: 37
holdout unique source groups: 18
holdout unique seeds: 9
holdout unique fault-family pairs: 7
holdout unique boundary axes: 3
holdout unique warm-up modes: 4
```

Snapshot reconstruction is complete:

```text
snapshot_lookup_rows: 110
missing_snapshots: 0
```

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

This supports the contract claim:

```text
M817 trained only a separate calibrator artifact.
```

## Gate Audit

Normal primary replay:

```text
train success_count: 57 / 57
train collision_count: 0
holdout success_count: 28 / 28
holdout collision_count: 0
```

Intervention replay:

```text
train baseline_collision_rate: 0.6783625730994152
train calibrated_collision_rate: 0.6783625730994152
holdout baseline_collision_rate: 0.7023809523809523
holdout calibrated_collision_rate: 0.7023809523809523
```

Old-behavior drift proxy:

```text
mean action drift: 8.148239589147847e-07
max action drift: 1.5842230141061009e-06
thresholds: mean <= 0.002, max <= 0.02
```

Gate summary:

```text
split_valid: pass
holdout_normal_collision_count: pass
holdout_intervention_collision_rate: pass
old_behavior_action_drift: pass
```

## Near-Identity Audit

The calibrator remained essentially identity:

```text
calibrator_mode: scalar_gate
initial_gate: 0.999
target_gate: 0.999
epoch 20 gate_mean: 0.998985767364502
epoch 20 gate_min: 0.9989854693412781
epoch 20 gate_max: 0.9989858269691467
```

This means M817 is a retention and harness pass, not an adaptive-control
breakthrough. It did not produce a meaningful gate change, margin lift, or
performance improvement. The correct interpretation is:

```text
the source-heldout calibration infrastructure is viable;
the near-identity candidate does not prove a useful learned calibrator.
```

## Supported Claims

M817 supports:

- the M814 adaptive primary corpus can be split into a source-heldout train and
  holdout set without losing source, fault, warm-up, or axis diversity;
- exact normal and intervention replay can be run on both splits;
- a separate residual calibrator can be trained without mutating the actor or
  M761 residual head;
- near-identity gating preserves normal primary rows, intervention collision
  sensitivity, and old-behavior action drift;
- the calibration harness is ready for a more informative follow-up design.

## Falsified Or Unsupported Claims

M817 does not support:

- that residual calibration improves driving performance;
- that the learned gate adapts meaningfully to source, fault, or boundary axis;
- that a vector or asymmetric gate is better than scalar identity;
- that PPO should start from this calibrator;
- that any driver checkpoint should be promoted;
- that current proxy fault variants are true wheel-level mechanical failures.

## Failure Taxonomy

No failure is assigned to M817's implementation result.

The main risk for the next milestone is:

```text
metric_artifact
```

because a calibrator can pass retention gates while being too close to identity
to carry new scientific evidence.

The secondary risks are:

```text
objective_overfit
behavior_regression
```

if a stronger follow-up objective improves train rows but breaks holdout rows,
old behavior, or intervention sensitivity.

## Decision

Decision:

```text
admit_adaptive_primary_calibration_followup_design
```

M818 admits a design-only follow-up. The next milestone should not run PPO or
promote. It should design a more informative non-PPO calibration probe that can
distinguish:

```text
identity retention
fixed residual scaling
source-heldout adaptive gating
vector/action-dimension gating
normal-margin lift versus intervention-sensitivity washout
```

Because the `v4_low_margin_new_data_route` branch is approaching its synthesis
cadence, the follow-up design should also route to branch synthesis before any
new implementation milestone.

Next blocker:

```text
m819-v4-adaptive-primary-calibration-followup-design
```
