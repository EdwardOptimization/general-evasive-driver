# M926 V4 Public-Base Residual Direction Feasibility Design

## Purpose

M926 opens the `v4_public_base_trust_region_feasibility` branch.

The previous branch showed:

```text
M919 can generate source-diverse M399-rooted target rows.
M921 target-action residual direction improves target MSE but not enough
  low-tail metrics inside normal retention.
M924 low-tail residual direction strongly improves low-tail metrics but leaves
  the normal-retention envelope.
```

M926 is design-only:

```text
no training
no new residual-head fitting
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Design Goal

Before training another residual objective, M927 should answer:

```text
Do existing residual directions contain any no-training mixture or alpha that
satisfies both normal-retention and low-tail objective gates?
```

This is a feasibility question, not a driver-improvement claim.

## Inputs

M927 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

full reconstruction corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

target rows:
  runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv

baseline metrics:
  runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv

residual heads:
  runs/m921_v4_public_base_regenerated_target_residual_probe/residual_head.pt
  runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/residual_head.pt
```

## Feasibility Sweep

M927 should load both residual heads and evaluate:

```text
direction_mix = (1 - w) * residual_M921 + w * residual_M924
```

with:

```text
mix_weights: 0.00, 0.10, 0.20, ..., 1.00
alphas:      0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35,
             0.50, 0.75, 1.00
```

For every pair, compute the same metrics as M921/M924:

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

No optimizer may run. This is a deterministic grid search over existing
directions.

## Candidate Gate

The feasibility candidate gate is the same as M921/M924:

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

If a candidate exists, M927 may only route to exact no-update compatibility
design. It must not run exact compatibility itself.

## Diagnostics

M927 should additionally report:

```text
best_normal_retaining_low_tail_row
best_tail_lift_nonretaining_row
normal_retention_boundary_row
target_loss_boundary_row
```

The goal is to identify whether the blocker is:

```text
1. direction infeasibility;
2. scale/alpha calibration;
3. target-action conflict;
4. too-strict normal-retention envelope;
5. active-set mismatch requiring row-local/corpus-level redesign.
```

## Required Outputs

M927 should write:

```text
runs/m927_v4_public_base_residual_direction_feasibility/summary.json
runs/m927_v4_public_base_residual_direction_feasibility/feasibility_grid.csv
runs/m927_v4_public_base_residual_direction_feasibility/objective_rows.csv
runs/m927_v4_public_base_residual_direction_feasibility/rejected_rows.csv
```

## Route Decision

If at least one candidate exists:

```text
route to exact no-update compatibility design for the best feasible mixture
```

If no candidate exists but a near-feasible row misses only target-action MSE:

```text
route to target/action conflict audit
```

If no candidate exists and all low-tail-improving rows violate normal retention:

```text
route to trust-region envelope audit or policy-level strategy
```

If no candidate exists and no row moves low-tail metrics:

```text
route away from residual-head bridge entirely
```

## Safeguards

M927 must not:

```text
train;
fit a new residual head;
update the M399 actor backbone;
change actor inputs;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
claim driver improvement.
```

## Decision

Decision:

```text
public_base_residual_direction_feasibility_design_admit_m927
```

Next:

```text
m927-v4-public-base-residual-direction-feasibility-implementation
```
