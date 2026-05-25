# M923 V4 Public-Base Alpha-Aware Low-Tail Objective Design

## Purpose

M923 designs the next objective after M921 showed that target-action imitation
alone does not produce enough normal-retained low-tail lift.

M923 is design-only:

```text
no training
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## M921 Failure Mode

M921 found:

```text
target-action loss improves at all alphas
low-tail metrics improve at larger alphas
normal retention fails at larger alphas
normal-retaining alphas do not produce enough low-tail lift
candidate_alpha_count = 0
```

This means the next objective should not simply increase the target-action loss
coefficient. The loss must directly optimize the metrics that blocked the gate
inside the normal-retention alpha range.

## Design Goal

M924 should answer:

```text
Can alpha-aware residual training improve low-tail p10, low-tail fraction, and
gap deficit at normal-retaining alphas better than target imitation alone?
```

The claim remains objective-only. No exact compatibility, replay, PPO, or
promotion can follow unless M924 finds an admitted objective alpha.

## Inputs

M924 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

full reconstruction corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

regenerated targets:
  runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv

baseline low-tail labels and metrics:
  runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
  runs/m909_v4_public_base_residual_head_probe/objective_rows.csv

M921 diagnostic:
  runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json
  runs/m921_v4_public_base_regenerated_target_residual_probe/alpha_metrics.csv
```

## Objective Structure

M924 should still train only a `feature_dim=128` residual head on frozen M399
features.

The key change is to compute the main loss at one or more training alphas in
the normal-retaining range:

```text
train_alphas: 0.20, 0.35
```

Rationale:

```text
alpha 0.35 was the largest normal-retaining alpha in M921.
alpha 0.20 was also normal-retaining and gives a more conservative trust-region
anchor.
```

For each train alpha:

```text
adjusted_normal = normal_action + alpha * residual(normal_features)
adjusted_intervention = intervention_action + alpha * residual(intervention_features)
gap = ||adjusted_intervention - adjusted_normal||
deficit = relu(target_gap - gap)
```

The loss should include:

```text
1. low-tail gap floor loss
   only on M912 low-tail rows:
   mean(relu(LOW_TAIL_GAP_THRESHOLD + margin - gap)^2)

2. low-tail deficit loss
   only on M912 low-tail rows:
   mean(relu(deficit - DEFICIT_TARGET)^2)

3. soft low-tail fraction surrogate
   sigmoid-based penalty for rows near the gap/deficit thresholds;
   this targets the M921 low_tail_fraction blocker directly.

4. target-action auxiliary
   M919 target action MSE, but with lower priority than the low-tail objective.

5. normal-retention anchor
   action drift and normal-anchor MSE at train alphas and final eval alphas.

6. intervention anchor
   keep residuals on intervention features bounded to avoid creating artificial
   gap lift through unstable intervention-side drift.
```

Suggested coefficients:

```text
low_tail_gap_floor_coef: 3.0
low_tail_deficit_coef: 2.0
low_tail_fraction_surrogate_coef: 1.0
target_action_coef: 0.5
normal_anchor_coef: 4.0
intervention_anchor_coef: 0.5
```

The exact values are pre-registered starting points, not promotion claims.

## Candidate Gate

M924 should keep the same candidate gates as M921:

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

M924 should also report whether the first normal-retaining alpha that improves
tail metrics is `0.20`, `0.35`, or another evaluation alpha.

## Evaluation Alphas

Evaluate:

```text
0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00
```

This keeps M924 comparable to M921.

## Required Outputs

M924 should write:

```text
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/summary.json
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/residual_head.pt
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/training_metrics.csv
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/alpha_metrics.csv
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/objective_rows.csv
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/target_weight_rows.csv
runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/rejected_rows.csv
```

The summary must include:

```text
train_alphas
low_tail_rows
joined_target_rows
candidate_alpha_count
candidate_alphas
best_normal_retaining_tail_alpha
actor_backbone_changed
training_started
m880_exact_used
replay_used
ppo_used
promoted
result_class
```

## Route Decision

If M924 finds an admitted alpha:

```text
route to M880 exact no-update compatibility design
```

If M924 improves target loss but still fails low-tail gates:

```text
route to branch synthesis before more narrow objective variants
```

If M924 improves low-tail gates only by breaking normal retention:

```text
route to residual trust-region design or lower action-cap target regeneration
```

## Safeguards

M924 must not:

```text
update the M399 actor backbone;
change actor inputs;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
claim driver improvement from objective-only residual metrics.
```

## Decision

Decision:

```text
public_base_alpha_aware_low_tail_objective_design_admit_m924
```

Next:

```text
m924-v4-public-base-alpha-aware-low-tail-residual-probe-implementation
```
