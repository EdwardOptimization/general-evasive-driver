# M1101 V4 Public Base Family-Aggregate Intersection Selector Design

## Purpose

M1101 designs a deterministic family-intersection selector over the M1099
replay-calibrated family-aggregate rows.

This milestone is design-only. It does not train, run PPO, run replay, run
objective optimization, mine rows, promote a checkpoint, use private holdout, or
change actor inputs.

## Motivation

M1099 showed that every row preserves the proof relation under its own source
policy:

```text
source rows: 146
normal successes: 146
wrong-history successes: 0
success drops: 146
```

M1100 then showed that direct mixed-source objective optimization is unsafe:
`13` family rows have cross-family failures under at least one non-source
policy. The all-policy intersection remains broad enough to use:

```text
all-policy pass rows: 133
physical pairs: 14
source labels: 4
targets: 3
left steps: 9
```

The selector should therefore filter to replay-calibrated rows that preserve
normal-history success and wrong-history failure across all public-base family
policies before any objective conversion.

## Inputs

Required inputs:

```text
runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv
runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv
runs/m1099_family_aggregate_replay_sanity/source_policy_gate_summary.csv
runs/m1099_family_aggregate_replay_sanity/summary.json
```

The selector must not call the replay runner. It should read existing M1099
artifacts only.

## Policy Family

The policy family is explicit and fixed by M1099:

```text
proof_current
short61049
short61050
short61051
```

Fail closed if any expected policy is missing from replay results for a
candidate row.

## Keep Rule

For each `family_row_id`, keep the row only if every policy in the family has a
replay result satisfying:

```text
normal_success == true
wrong_history_success == false
success_drop == true
normal_margin is finite
wrong_history_margin is finite
margin_gap is finite
```

The source-policy row must also satisfy the same relation. This is redundant
after M1099 but should remain a hard check so the selector is self-contained.

Rows failing any policy are written to a drop report, not silently discarded.

## Output Contract

The implementation should write:

```text
runs/m1102_family_aggregate_intersection_selector/family_intersection_rows.csv
runs/m1102_family_aggregate_intersection_selector/dropped_cross_family_rows.csv
runs/m1102_family_aggregate_intersection_selector/policy_pass_matrix.csv
runs/m1102_family_aggregate_intersection_selector/source_summary.csv
runs/m1102_family_aggregate_intersection_selector/target_summary.csv
runs/m1102_family_aggregate_intersection_selector/summary.json
```

`family_intersection_rows.csv` should preserve all M1097 row metadata:

```text
family_row_id
source_row_index
source_checkpoint_label
source_checkpoint_path
source_checkpoint_family
physical_pair_key
boundary_geometry_key
duplicate_geometry_group_id
duplicate_geometry_group_size
duplicate_geometry_source_labels
target
left_seed/right_seed
left_step/right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
```

It should append replay-calibration fields:

```text
family_policy_count
family_policy_pass_count
min_normal_margin
max_wrong_history_margin
min_margin_gap
mean_margin_gap
failed_policy_labels
```

## Diversity Gate

The selector should fail closed unless the kept rows satisfy:

```text
rows >= 80
physical_pairs >= 10
source_labels >= 4
targets >= 3
left_steps >= 8
max_physical_pair_fraction <= 0.20
max_source_label_fraction <= 0.45
```

These thresholds preserve the M1092/M1097 robustness intent without pretending
that cross-family failures did not happen.

## Dropped-Row Classification

Every dropped row should include one or more failure reasons:

```text
missing_policy_replay
normal_history_failure
wrong_history_success
nonfinite_margin
source_policy_failure
```

The report should also preserve failed policy labels and the original
source-checkpoint label so later audits can distinguish source-specific rows
from broad proof failures.

## Safety

The selector must not:

```text
train
run PPO
run replay
run objective optimization
mine rows
write mixed-source objective NPZ
promote a checkpoint
use private holdout
change actor inputs
```

## Decision

```text
family_aggregate_intersection_selector_design_admit_implementation
```

Next:

```text
m1102-v4-public-base-family-aggregate-intersection-selector-implementation
```

M1102 should implement this selector, run it on M1099 artifacts, and stop before
objective conversion. If the diversity gate unexpectedly fails, route to
source-specific objective corpora design instead of weakening thresholds.

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
