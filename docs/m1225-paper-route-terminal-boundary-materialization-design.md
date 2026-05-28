# M1225 Paper-Route Terminal-Boundary Materialization Design

## Summary

M1225 designs the new `paper_route_terminal_boundary_materialization` branch
selected by M1224.

Decision:

```text
terminal_boundary_materialization_design_admit_adapter_export
```

No source mining, relocation replay, outcome intervention, training, PPO,
checkpoint repair, promotion, private holdout, profile tuning, or actor-input
change occurs in M1225.

## Design Question

M1222 produced action-divergent wrong-history rows but no outcome degradation:

```text
all_action_threshold_rows: 274
margin_gap >= 0.010 rows:    0
success_drop_rows:           0
```

The new branch asks:

```text
Can those action-divergent rows be materialized into terminal-margin or
success-critical wrong-history rows by bounded obstacle/timing relocation,
without changing actor inputs or training the actor?
```

## Compatibility Audit

Existing relocation runner:

```text
autodrift.source_balanced_boundary_relocation_surface
```

It expects candidate rows with fields such as:

```text
checkpoint_label
variant
left_seed / left_step
right_seed / right_step
target
normal_margin
margin_gap
first_action_distance
action_trajectory_distance_mean
source obstacle geometry fields
```

M1222 `candidate_scores.csv` has the important information but not under the
exact legacy field names:

```text
surface
target
variant
left_seed / left_step
right_seed / right_step
left_obstacle_x_m / left_obstacle_y_m
left_obstacle_distance
normal_success / wrong_success
normal_margin / wrong_margin
margin_gap
wrong_first_action_l2
wrong_action_sequence_mean_l2
wrong_action_sequence_max_l2
preferred_vs_rejected_action_mean_l2
preferred_vs_rejected_action_max_l2
```

Therefore M1222 rows should not be fed directly to the relocation runner.

Selected route:

```text
M1226 implements a small adapter/exporter from M1222 candidate_scores.csv to a
relocation-compatible action-divergent candidate CSV.
```

## Adapter Contract

M1226 should read:

```text
runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv
```

It should filter rows by the pre-registered M1222 action criteria:

```text
variant == wrong_matched_history
normal_success == true
normal_margin >= 0.0
normal_margin <= 1.0
wrong_first_action_l2 >= 0.002
wrong_action_sequence_mean_l2 >= 0.006
preferred_vs_rejected_action_mean_l2 >= 0.010
```

It should write:

```text
runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv
runs/m1226_terminal_boundary_candidate_export/candidate_pool.csv
runs/m1226_terminal_boundary_candidate_export/rejected_candidates.csv
runs/m1226_terminal_boundary_candidate_export/summary.json
```

The exported `candidate_outcomes.csv` should include at least:

```text
checkpoint_label = l3_s111602
variant = wrong_matched_history
left_seed, left_step, right_seed, right_step
target
normal_success
variant_success from wrong_success
success_drop
normal_margin
variant_margin from wrong_margin
margin_gap
normal_better
first_action_distance from wrong_first_action_l2
action_trajectory_distance_mean from preferred_vs_rejected_action_mean_l2
action_trajectory_distance_max from preferred_vs_rejected_action_max_l2
source_obstacle_body_x from left_obstacle_x_m
source_obstacle_body_y from left_obstacle_y_m
source_obstacle_distance from left_obstacle_distance
source_obstacle_lateral_offset from left_obstacle_y_m
physical_pair_key
source_obstacle_bucket
_candidate_export_index
```

It may include pass-through diagnostics:

```text
context_distance
response_distance
hidden_distance
obstacle_x_abs_delta
obstacle_y_abs_delta
step_abs_delta
sequence_length
rejection_reason
```

## Source-Diversity Gate For Adapter

M1226 should pass only if the exported candidate set is source-diverse:

```text
selected_rows >= 120
selected_physical_pairs >= 40
selected_left_seeds >= 6
selected_right_seeds >= 15
selected_left_steps >= 4
selected_targets >= 2
selected_source_obstacle_buckets >= 4
max_rows_per_physical_pair_fraction <= 0.05
max_left_seed_share <= 0.40
max_target_share <= 0.70
```

This is intentionally stricter than M1177's failed artifact path on physical
pair dominance, because M1222 already has explicit geometry and many physical
pairs.

Current M1222 all-action-threshold diagnostics support trying this:

```text
rows:            274
physical pairs:   85
left seeds:        7
right seeds:      24
targets:           2
max physical pair share: 0.0255
max left seed share:     0.3650
max target share:        0.6423
```

## Future Relocation Run Shape

If M1226 passes, a later M1227 should run bounded relocation with one current
checkpoint:

```text
checkpoint-policy:
  l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt

env config:
  configs/paper_route_corrected_profiles/m1207_l3_online_gru.json

outcome/candidate csv:
  runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv
```

Initial relocation constraints:

```text
delay_steps: 10
max_continuation_steps: 60
target_normal_margins: 0.0005,0.001,0.002,0.003,0.005,0.0075,0.010,0.015,0.020
half_width_inflations: 0,0.10,0.20
body_longitudinal_offsets: -4,-2,0,2,4
body_lateral_offsets: -0.5,-0.25,0,0.25,0.5
min_normal_margin: 0.0
max_normal_margin: 0.20
min_margin_gap: 0.010
report_variants: wrong_matched_history
```

This is a bounded materialization test, not broad scenario generation.

## Relocation Pass Criteria

A later relocation run may pass only if it produces source-diverse accepted
wrong-history rows:

```text
accepted_wrong_rows >= 80
accepted_wrong_physical_pairs >= 10
accepted_wrong_left_steps >= 5
accepted_wrong_targets >= 2
accepted_wrong_source_obstacle_buckets >= 4
accepted_wrong_normal_margin_buckets >= 2
accepted_wrong_success_drop_fraction >= 0.50
mean accepted margin gap >= 0.010
max_rows_per_physical_pair_fraction <= 0.15
control_accepted_wrong_rows == 0 if a control is included
```

If accepted rows collapse to one physical pair, one target, or one obstacle
bucket, the result is a failure even if row count is high.

## Rejected Shortcuts

Do not:

- train from M1222 action-divergent rows;
- run relocation before the adapter/source-budget export passes;
- weaken M1222 action thresholds;
- accept action divergence without margin or success degradation;
- claim self-identification from materialization design;
- ignore the M1177 active-set collapse lesson.

## Decision

```text
terminal_boundary_materialization_design_admit_adapter_export
```

Next blocker:

```text
m1226-paper-route-terminal-boundary-candidate-export
```
