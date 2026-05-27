# M1139 V4 Public Base Row15 Promoted Intersection Selector

## Purpose

M1139 runs the M1138 pre-registered deterministic family-intersection selector
over the M1136 cross-family replay artifacts.

This milestone is selector/export only. It does not run replay, optimize an
objective, train actor weights, run PPO, promote a checkpoint, use private
holdout, or change actor inputs.

## Command Result

Artifact:

```text
runs/m1139_row15_promoted_intersection_selector/summary.json
```

Top-level result:

```text
decision: family_aggregate_intersection_selector_pass
passed: true
family_rows: 172
replay_rows: 860
kept_rows: 148
dropped_rows: 24
training_started: false
ppo_used: false
replay_started: false
objective_optimization_started: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

## Diversity Gate

The selector kept rows that pass normal-history success, wrong-history failure,
and success-drop checks under all five expected policies:

```text
row15_current
previous_m1078_base
short61049
short61050
short61051
```

Selected-row diversity:

```text
rows: 148
physical_pairs: 13
source_labels: 5
targets: 2
left_steps: 6
max_physical_pair_rows: 20
max_physical_pair_fraction: 0.135135
max_source_label_rows: 42
max_source_label_fraction: 0.283784
gate_pass: true
```

This satisfies the pre-registered thresholds:

```text
rows >= 100
physical_pairs >= 12
source_labels >= 4
targets >= 2
left_steps >= 6
max_physical_pair_fraction <= 0.25
max_source_label_fraction <= 0.45
```

## Source Summary

```text
previous_m1078_base: 5 rows, 3 physical pairs, 1 target, 2 left steps
row15_current:       28 rows, 5 physical pairs, 2 targets, 4 left steps
short61049:          41 rows, 11 physical pairs, 2 targets, 6 left steps
short61050:          32 rows, 9 physical pairs, 2 targets, 6 left steps
short61051:          42 rows, 11 physical pairs, 2 targets, 6 left steps
```

Minimum margin gaps remain finite and positive across all sources:

```text
previous_m1078_base: 0.001594668
row15_current:       0.001595020
short61049:          0.001313556
short61050:          0.001313399
short61051:          0.001313491
```

## Target Summary

The all-policy intersection retains braking and yaw-response targets:

```text
future_braking_deceleration:
  rows: 78
  physical_pairs: 9
  source_labels: 5
  left_steps: 5
  min_margin_gap: 0.001313399

future_yaw_response:
  rows: 70
  physical_pairs: 4
  source_labels: 4
  left_steps: 2
  min_margin_gap: 0.003805305
```

The selector intentionally reports that lateral-acceleration rows do not survive
the all-policy intersection. This is not a failure because the M1138 threshold
was `targets >= 2`, reflecting the M1137 audit result.

## Outputs

```text
runs/m1139_row15_promoted_intersection_selector/family_intersection_rows.csv
runs/m1139_row15_promoted_intersection_selector/dropped_cross_family_rows.csv
runs/m1139_row15_promoted_intersection_selector/policy_pass_matrix.csv
runs/m1139_row15_promoted_intersection_selector/source_summary.csv
runs/m1139_row15_promoted_intersection_selector/target_summary.csv
runs/m1139_row15_promoted_intersection_selector/summary.json
```

## Interpretation

M1139 converts the M1136/M1137 cross-family replay report into a deterministic
all-policy proof surface. This removes rows that are source-policy valid but not
family-intersection valid, and it keeps a broad enough surface for single
target-policy materialization.

The result does not support direct mixed-family objective optimization. The next
step must materialize these rows under one target policy, using the current
public-gate base hidden-state/action/margin space.

## Decision

```text
row15_promoted_intersection_selector_pass_route_to_target_materialization_design
```

Next:

```text
m1140-v4-public-base-row15-promoted-target-materialization-design
```
