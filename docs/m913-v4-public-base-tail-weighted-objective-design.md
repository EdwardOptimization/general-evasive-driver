# M913 V4 Public-Base Tail-Weighted Objective Design

## Purpose

M913 designs the next residual-head-only objective after M912 found a broad
M399 low-tail failure:

```text
low_tail_rows: 498 / 1213
distinct_fault_family_pairs: 17
route_decision: public_base_tail_weighted_objective_design
```

M913 is design-only:

```text
no training
no actor update
no M880 exact execution
no replay
no PPO
no checkpoint promotion
```

## Core Design

M914 should train only a new residual head on frozen M399 recurrent actor
features. It should not update the M399 actor.

Compared with M909, M914 changes the residual objective, not the actor contract:

```text
base actor: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
actor contract: P0 human-view no-wheel 72-dim frame
actor feature_dim: 128
trainable scope: residual head only
forbidden: actor update, replay, PPO, promotion
```

## Required Inputs

M914 should consume:

```text
M399 base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

M755 sequence corpus:
  runs/m755_v4_sequence_outcome_corpus_export/summary.json
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

M912 recalibration outputs:
  runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
  runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv

M909 diagnostic rows:
  runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
```

The M912 low-tail rows do not include every field needed to reconstruct M755
samples. M914 should join low-tail membership back to the M755 positive rows by:

```text
contrast_group_id
source_index
variant
horizon
```

If the join drops rows, M914 must stop and write rejected rows. It must not
silently train on a partial low-tail set.

## Tail Weights

M914 should assign a row weight to every reconstructed sample:

```text
base_weight = outcome_weight(row)
tail_indicator = 1 if row is in M912 low_tail_rows else 0
deficit = max(M909 near-base gap_deficit for row, 0)
deficit_bonus = clip(50 * deficit, 0, 3)
tail_weight = base_weight * (1 + 4 * tail_indicator + deficit_bonus)
tail_weight = clip(tail_weight, 1, 8)
```

The intent is:

```text
low-tail rows are first-class training targets;
large-deficit rows get stronger pressure;
non-low-tail rows still retain coverage so the residual does not become a
single-surface patch.
```

## Loss Terms

M914 should train a `feature_dim=128` residual head with the same bounded
residual architecture as M761/M909:

```text
Linear(128, 64) -> Tanh -> Linear(64, 3)
max_residual: 0.04
```

The loss should be:

```text
normal_zero_loss =
  mean(||delta_normal||^2)

tail_gap_loss =
  weighted_mean(tail_weight * relu(target_gap - adjusted_gap)^2)

low_tail_floor_loss =
  weighted_mean(tail_weight * relu(0.021141 - adjusted_gap)^2)
  over low-tail rows only

intervention_anchor_loss =
  mean(||delta_intervention||^2)

hard_negative_loss =
  same hard-negative calibration loss as M761/M909

loss =
  3.0 * normal_zero_loss
  + 1.0 * tail_gap_loss
  + 1.0 * low_tail_floor_loss
  + 0.25 * intervention_anchor_loss
  + 0.10 * hard_negative_loss
```

The key change from M909 is that low-tail rows and p10/floor behavior are
directly represented in the training objective. M914 must not optimize only
mean gap.

## Alpha Ladder

M914 should evaluate:

```text
0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00
```

The lower alphas preserve comparability with M909. The intermediate `0.35` and
`0.75` values help locate a candidate before normal-retention failure.

## Candidate Admission Gates

M914 should export alpha metrics and admit a candidate only if all gates pass:

```text
actor_backbone_changed == false
residual_only_training == true
residual_head.feature_dim == 128
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
training_started == true
ppo_used == false
promoted == false
```

Normal-retention gate:

```text
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 <= 0.000025
first_action_drift_from_base_mean <= 0.003
first_action_drift_from_base_p95 <= 0.008
```

Public-base tail-lift gate:

```text
near_base_gap_p10 = 0.0069862247444689276
near_base_gap_deficit_mean = 0.016876555956218328
near_base_low_tail_fraction = 0.4105523495465787

candidate_gap_p10 >= near_base_gap_p10 + 0.004
candidate_gap_deficit_mean <= near_base_gap_deficit_mean - 0.002
candidate_low_tail_fraction <= near_base_low_tail_fraction - 0.05
```

The candidate is not a public-base integration candidate yet. It is only an
admitted residual-head objective candidate for later no-update compatibility
checks.

## M914 Outputs

M914 should write:

```text
runs/m914_v4_public_base_tail_weighted_residual_probe/summary.json
runs/m914_v4_public_base_tail_weighted_residual_probe/residual_head.pt
runs/m914_v4_public_base_tail_weighted_residual_probe/alpha_metrics.csv
runs/m914_v4_public_base_tail_weighted_residual_probe/objective_rows.csv
runs/m914_v4_public_base_tail_weighted_residual_probe/training_metrics.csv
runs/m914_v4_public_base_tail_weighted_residual_probe/rejected_rows.csv
```

`alpha_metrics.csv` must include:

```text
normal_intervention_gap_p10
gap_deficit_mean
low_tail_rows
low_tail_fraction
normal_retention_pass
tail_lift_pass
exact_probe_candidate
```

## Failure Routing

If M914 finds no candidate alpha:

```text
route to public-base target regeneration design
```

Do not keep increasing weights or epochs indefinitely. M912 already showed the
low-tail set is broad; if a first tail-weighted residual probe cannot move it
under normal retention, the target/action generation itself likely needs
refreshing from M399 rollouts.

If M914 finds a candidate alpha:

```text
route to no-training M880 exact compatibility design
```

Even then, replay, PPO, and promotion remain blocked until exact compatibility
and later replay/proof gates pass.

## Supported Claims

M913 supports:

```text
1. The next implementation should be residual-head-only and M399-frozen.
2. The new objective should explicitly weight M912 low-tail rows.
3. Admission must require p10, deficit, low-tail fraction, and normal-retention
   gates.
```

## Unsupported Claims

M913 does not support:

```text
tail-weighted residual success;
M880 exact compatibility;
replay retention;
PPO safety;
public-base promotion.
```

## Decision

Decision:

```text
public_base_tail_weighted_objective_design_admit_m914
```

Next:

```text
m914-v4-public-base-tail-weighted-residual-probe-implementation
```

M914 may train a residual head only. It must keep the M399 actor frozen and
must not run M880 exact compatibility, replay, PPO, or promotion.
