# M920 V4 Public-Base Regenerated-Target Residual Objective Design

## Purpose

M920 designs the first residual-head objective that uses the M919 regenerated
target corpus.

M919 produced:

```text
accepted_targets: 122
strict_low_tail_accepted_targets: 103
near_tail_accepted_targets: 19
distinct_fault_family_pairs: 14
distinct_seeds: 26
max_fault_family_pair_fraction: 0.19672131147540983
```

M920 is design-only:

```text
no residual-head training
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Design Goal

The next question is:

```text
Can a frozen-M399 residual head trained on M919 regenerated target actions
improve low-tail sequence-objective metrics while preserving normal-action
retention?
```

This is still an objective-only probe. It must not update the M399 actor
backbone.

## Inputs

M921 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

scenario config:
  configs/extreme_fault_distribution_v4_scenarios.json

full reconstruction corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

regenerated target corpus:
  runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv
  runs/m919_v4_public_base_expanded_target_regeneration/summary.json

low-tail and baseline metrics:
  runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
  runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
```

## Model Constraint

M921 may train only a residual head over frozen M399 features:

```text
feature_dim: 128
actor_backbone: frozen
deployable_actor_input: unchanged P0 human-view 72-dim + GRU
```

It must save the residual head separately and report both actor checksum before
and after.

## Objective

M921 should train a residual head with three loss groups:

```text
1. regenerated target action loss
   target_action from M919 accepted_target_rows
   strict_low_tail rows weight >= near_tail rows

2. normal-retention anchor
   keep adjusted normal action close to M399 base action on the full 1213-row
   reconstruction corpus

3. sequence gap objective
   preserve or improve normal/intervention gap and low-tail metrics from the
   M912/M909 near-base baseline
```

Suggested weights:

```text
strict_low_tail_target_weight: 2.0
near_tail_target_weight: 0.75
normal_anchor_coef: 3.0
gap_floor_coef: 1.0
intervention_anchor_coef: 0.25
```

The target-action loss should be evaluated only on M919 accepted target keys.
Normal-retention metrics must still be evaluated over the full reconstructed
M755 corpus.

## Alpha Evaluation

Evaluate interpolation alphas:

```text
0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00
```

For each alpha, write:

```text
normal_anchor_mse_mean
normal_anchor_mse_p95
first_action_drift_from_base_mean
first_action_drift_from_base_p95
normal_intervention_gap_p10
gap_deficit_mean
low_tail_fraction
target_action_mse_mean
strict_target_action_mse_mean
near_tail_target_action_mse_mean
```

## Candidate Gate

An alpha is an admitted objective candidate only if:

```text
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 <= 0.000025
first_action_drift_from_base_mean <= 0.003
first_action_drift_from_base_p95 <= 0.008
normal_intervention_gap_p10 >= M912 near_base_gap_p10 + 0.004
gap_deficit_mean <= M912 near_base_gap_deficit_mean - 0.002
low_tail_fraction <= M912 low_tail_fraction - 0.05
target_action_mse_mean improves versus alpha 0.0
strict_target_action_mse_mean improves versus alpha 0.0
```

If no alpha passes, M921 should route to target/objective audit rather than
M880 exact compatibility.

## Required Outputs

M921 should write:

```text
runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json
runs/m921_v4_public_base_regenerated_target_residual_probe/residual_head.pt
runs/m921_v4_public_base_regenerated_target_residual_probe/training_metrics.csv
runs/m921_v4_public_base_regenerated_target_residual_probe/alpha_metrics.csv
runs/m921_v4_public_base_regenerated_target_residual_probe/objective_rows.csv
runs/m921_v4_public_base_regenerated_target_residual_probe/target_weight_rows.csv
runs/m921_v4_public_base_regenerated_target_residual_probe/rejected_rows.csv
```

## Route Decision

If M921 finds at least one admitted alpha:

```text
route to M880 exact no-update compatibility design for the selected alpha
```

If no alpha passes because target loss improves but tail metrics do not:

```text
route to regenerated-target objective audit
```

If no alpha passes because normal retention fails:

```text
route to residual trust-region or lower-cap target action design
```

## Safeguards

M921 must not:

```text
update the M399 actor backbone;
change actor inputs;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
claim driver improvement from an objective-only residual probe.
```

## Decision

Decision:

```text
public_base_regenerated_target_residual_objective_design_admit_m921
```

Next:

```text
m921-v4-public-base-regenerated-target-residual-probe-implementation
```
