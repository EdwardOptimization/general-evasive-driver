# M1142 V4 Public Base Row15 Promoted Target Materialization

## Purpose

M1142 runs the M1140/M1141-admitted target-policy materializer for the M1139
all-policy intersection rows under `row15_current`.

This milestone runs materialization only. It does not run replay, optimize an
objective, train actor weights, run PPO, mine rows, promote a checkpoint, use
private holdout, write an objective NPZ, or change actor inputs.

## Command Result

Artifact:

```text
runs/m1142_row15_promoted_target_materialization/row15_current_materialization_summary.json
```

Top-level result:

```text
decision: target_policy_materialization_pass
passed: true
target_policy_label: row15_current
rows: 148
expected_rows: 148
normal_success_count: 148
wrong_history_success_count: 0
success_drop_count: 148
finite_objective_rows: 148
training_started: false
ppo_used: false
replay_started: false
objective_optimization_started: false
objective_npz_written: false
mining_started: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

## Diversity Gate

```text
rows: 148
physical_pairs: 13
source_labels: 5
targets: 2
left_steps: 6
max_physical_pair_fraction: 0.135135
max_source_label_fraction: 0.283784
gate_pass: true
```

This satisfies the M1140 thresholds:

```text
rows == 148
physical_pairs >= 12
source_labels >= 4
targets >= 2
left_steps >= 6
max_physical_pair_fraction <= 0.25
max_source_label_fraction <= 0.45
```

## Source Summary

All rows now use `row15_current` target-policy replay margins/actions while
preserving source labels as provenance:

```text
previous_m1078_base: 5 rows, 3 physical pairs, 1 target, 2 left steps
row15_current:       28 rows, 5 physical pairs, 2 targets, 4 left steps
short61049:          41 rows, 11 physical pairs, 2 targets, 6 left steps
short61050:          32 rows, 9 physical pairs, 2 targets, 6 left steps
short61051:          42 rows, 11 physical pairs, 2 targets, 6 left steps
```

Target-policy margin safety remains finite:

```text
minimum normal margin:       0.000997985
maximum wrong-history margin: -0.000063233
minimum margin gap:          0.001313707
```

## Target Summary

```text
future_braking_deceleration:
  rows: 78
  physical_pairs: 9
  source_labels: 5
  left_steps: 5
  normal_margin_min: 0.000997985
  wrong_history_margin_max: -0.000063233
  margin_gap_min: 0.001313707

future_yaw_response:
  rows: 70
  physical_pairs: 4
  source_labels: 4
  left_steps: 2
  normal_margin_min: 0.002261427
  wrong_history_margin_max: -0.000438606
  margin_gap_min: 0.003827795
```

## Outputs

```text
runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
runs/m1142_row15_promoted_target_materialization/row15_current_source_summary.csv
runs/m1142_row15_promoted_target_materialization/row15_current_target_summary.csv
runs/m1142_row15_promoted_target_materialization/row15_current_materialization_summary.json
```

No objective NPZ was written.

## Interpretation

M1142 validates that the M1139 all-policy surface can be materialized into one
current-base target-policy row space. This removes the main hidden-state/action
mixing blocker before objective corpus construction.

The result does not prove objective learnability, actor improvement, PPO
readiness, promotion readiness, private-holdout generalization, paper-level
evidence, or level3 anticipatory self-identification.

## Decision

```text
row15_promoted_target_materialization_pass_route_to_objective_corpus_design
```

Next:

```text
m1143-v4-public-base-row15-promoted-objective-corpus-design
```
