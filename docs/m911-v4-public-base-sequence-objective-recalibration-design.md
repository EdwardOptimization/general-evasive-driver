# M911 V4 Public-Base Sequence Objective Recalibration Design

## Purpose

M911 designs the no-training recalibration step after M910.

The problem is now:

```text
M399 can train a 128-dim residual head, but the M761-style objective produces
candidate_alpha_count = 0.
```

M911 is design-only:

```text
no training
no actor update
no M880 exact execution
no replay
no PPO
no checkpoint promotion
```

## Design Goal

Before training another residual head or touching M880 pair-delta exact checks,
we need a public-base-specific audit that answers:

```text
Which rows cause M399's low-tail gap failure?
Are those rows source/fault/variant diverse enough to justify a new
tail-weighted objective?
Or are the old M755/M758 targets too M568-specific, requiring target
regeneration from M399 rollouts?
```

## Inputs

M912 should consume:

```text
M399 run:
  runs/m909_v4_public_base_residual_head_probe/summary.json
  runs/m909_v4_public_base_residual_head_probe/alpha_metrics.csv
  runs/m909_v4_public_base_residual_head_probe/objective_rows.csv

M568 reference:
  runs/m761_v4_sequence_objective_probe/summary.json
  runs/m761_v4_sequence_objective_probe/alpha_metrics.csv
```

M912 must not load a checkpoint or train a model. It should be a deterministic
CSV/JSON audit.

## Near-Base Diagnostic Alpha

M909 did not export alpha `0.0` rows. The lowest available alpha is:

```text
alpha = 0.02
```

At this alpha, normal drift is small:

```text
first_action_drift_from_base_mean: 0.0002048
first_action_drift_from_base_p95: 0.0005098
normal_retention_pass: true
```

M912 may use alpha `0.02` as a near-base diagnostic, but it must label it
explicitly as:

```text
near_base_alpha: 0.02
not exact alpha 0.0
```

This prevents later claims from treating it as a true residual-free baseline.

## Required M912 Outputs

M912 should write:

```text
runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
runs/m912_v4_public_base_sequence_recalibration_audit/alpha_comparison.csv
runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv
```

The audit should also be documented in:

```text
docs/m912-v4-public-base-sequence-recalibration-audit.md
```

## Alpha Comparison

`alpha_comparison.csv` should compare M761 and M909 by alpha:

```text
alpha
m761_retention_pass
m761_gap_lift_pass
m761_gap_p10
m761_gap_deficit_mean
m761_first_action_drift_mean
m909_retention_pass
m909_gap_lift_pass
m909_gap_p10
m909_gap_deficit_mean
m909_first_action_drift_mean
gap_p10_delta_m909_minus_m761
deficit_delta_m909_minus_m761
```

This makes the M910 observation machine-checkable:

```text
M909 mean gap is high, but p10 and deficit remain poor.
```

## Low-Tail Row Definition

For the near-base alpha `0.02`, mark a row as low-tail if either condition
holds:

```text
normal_intervention_gap < 0.021141
gap_deficit > 0.02
```

`0.021141` is the M761 baseline p10 reference. In M912 it is a diagnostic
threshold, not a pass/fail promotion gate.

`low_tail_rows.csv` should include:

```text
contrast_group_id
source_index
seed
step
preferred_fault_family
wrong_fault_family
fault_family_pair
variant
horizon
source_pool
claim_boundary_level
normal_intervention_gap
target_gap
gap_deficit
hard_negative_calibration_loss
low_tail_reason
```

## Group Deficit Summary

`group_deficit_summary.csv` should summarize low-tail coverage by:

```text
preferred_fault_family
wrong_fault_family
fault_family_pair
variant
horizon
source_pool
claim_boundary_level
```

For each group, record:

```text
rows
low_tail_rows
low_tail_fraction
gap_mean
gap_p10
gap_deficit_mean
hard_negative_calibration_loss_mean
```

## Route Decision Rules

M912 should choose exactly one route.

Route A:

```text
public_base_tail_weighted_objective_design
```

Use this if low-tail rows are broad enough to support objective design:

```text
low_tail_rows >= 100
distinct_fault_family_pairs >= 3
distinct_variants >= 1
distinct_source_pools >= 1
```

This route means the old corpus is still useful, but M399 needs a tail-weighted
loss focused on the rows that remain deficient.

Route B:

```text
public_base_target_regeneration_design
```

Use this if low-tail rows are too concentrated or inconsistent:

```text
low_tail_rows < 100
or distinct_fault_family_pairs < 3
```

This route means M755/M758 targets are too stale for M399 and should be
regenerated from M399 rollouts before another residual/head/objective attempt.

Route C:

```text
residual_free_public_base_sanity_design
```

Use this only if near-base alpha is already strong:

```text
near_base_gap_p10 >= 0.021141
and near_base_gap_deficit_mean <= 0.014809
```

M910 already suggests this route is unlikely, but M912 should keep it explicit.

## Safeguards

M912 must not:

```text
train a residual head;
update actor parameters;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
convert M568/M761 thresholds into public-base pass gates;
claim M909 residual head is admitted.
```

## Supported Claims

M911 supports:

```text
1. The next step should be deterministic recalibration/audit, not another
   residual training run.
2. M399 needs row-level low-tail diagnosis before M880 exact integration.
3. The route decision can be made from saved M909/M761 artifacts without new
   training.
```

## Unsupported Claims

M911 does not support:

```text
M399 recalibration result;
new residual objective feasibility;
target regeneration success;
M880 exact compatibility;
replay retention;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_sequence_recalibration_design_admit_m912
```

Next:

```text
m912-v4-public-base-sequence-recalibration-audit-implementation
```

M912 should implement and run the no-training recalibration audit described
above.
