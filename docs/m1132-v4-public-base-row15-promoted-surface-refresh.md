# M1132 V4 Public Base Row15 Promoted Surface Refresh

## Purpose

M1132 runs the M1131 pre-registered fresh source-diverse protected/preference
surface refresh for the M1129 alpha `0.15` public-gate base.

This milestone runs mining/evaluation only. It does not train actor weights,
run PPO, run objective optimization, promote a checkpoint, use private holdout,
or change actor inputs.

## Stage 1: Matched-Current Ambiguity

Artifact:

```text
runs/m1132_row15_promoted_matched_current_seed113200/summary.json
```

Result:

```text
candidate_pair_count: 471690
accepted_pair_count: 3103
accepted_physical_pair_count: 190
accepted_left_step_count: 26
accepted_source_obstacle_bucket_count: 16
accepted_by_target:
  future_braking_deceleration: 1182
  future_yaw_response: 1505
  future_lateral_accel_response: 416
ambiguity_surface_found: true
```

The promoted base family has ample matched-current ambiguity candidates.

## Stage 2: Matched-History Outcome Gate

Artifact:

```text
runs/m1132_row15_promoted_outcome_seed113200/summary.json
```

Result:

```text
input_pair_count: 3103
outcome_row_count: 18618
outcome_summary_rows: 90
outcome_interventions_csv:
  runs/m1132_row15_promoted_outcome_seed113200/outcome_interventions.csv
```

The outcome gate generated enough continuation rows for source-balanced boundary
relocation.

## Stage 3: Source-Balanced Boundary Relocation

Artifact:

```text
runs/m1132_row15_promoted_source_balanced_surface_seed113200/summary.json
```

Source budget:

```text
candidate_wrong_history_rows: 3103
eligible_physical_pairs: 190
eligible_left_steps: 26
eligible_checkpoints: 5
eligible_targets: 3
max_candidate_pair_fraction: 0.006445
source_budget_ready: true
```

Candidate selection:

```text
selected_rows: 1024
selected_physical_pairs: 190
selected_left_steps: 26
selected_targets: 3
max_selected_rows_per_physical_pair: 6
max_selected_pair_fraction: 0.005859
decision: source_balanced_candidates_ready
```

Balanced accepted wrong-history surface:

```text
accepted_wrong_rows: 172
accepted_wrong_physical_pairs: 15
accepted_wrong_left_steps: 6
accepted_wrong_checkpoints: 5
accepted_wrong_targets: 3
accepted_wrong_normal_margin_buckets: 3
accepted_wrong_success_drop_fraction: 1.0
accepted_wrong_normal_margin_min: 0.000814
accepted_wrong_normal_margin_mean: 0.002205
accepted_wrong_normal_margin_max: 0.011606
accepted_wrong_margin_gap_mean: 0.004526
accepted_wrong_margin_gap_max: 0.012646
max_rows_per_physical_pair_fraction: 0.116279
control_accepted_wrong_rows: 0
decision: source_balanced_boundary_export_pass
passed: true
```

All pre-registered acceptance criteria pass:

```text
accepted_wrong_history_rows >= 100
accepted_wrong_physical_pairs >= 12
accepted_wrong_left_steps >= 6
accepted_wrong_checkpoints >= 4
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 2
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
control_accepted_wrong_rows == 0
```

Exported surface:

```text
runs/m1132_row15_promoted_source_balanced_surface_seed113200/balanced_accepted_wrong_history_rows.csv
```

## Interpretation

M1132 confirms that the promoted alpha `0.15` public-gate base still exposes a
fresh, source-diverse wrong-history boundary surface. This reduces the risk
that the M1129 promoted base is only passing stale public rows.

The result is still public proof-surface evidence. It does not prove PPO
readiness, private-holdout generalization, paper-level generalization,
real-vehicle transfer, or level3 anticipatory self-identification.

## Decision

```text
row15_promoted_surface_refresh_pass_route_to_compact_conversion_design
```

Next:

```text
m1133-v4-public-base-row15-promoted-compact-conversion-design
```
