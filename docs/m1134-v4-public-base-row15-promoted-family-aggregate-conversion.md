# M1134 V4 Public Base Row15 Promoted Family Aggregate Conversion

## Purpose

M1134 runs the M1133 pre-registered export-only family aggregate conversion for
the M1132 promoted-base source-balanced surface.

This milestone does not run replay, optimize an objective, train actor weights,
run PPO, promote a checkpoint, use private holdout, or change actor inputs.

## Input

```text
runs/m1132_row15_promoted_source_balanced_surface_seed113200/balanced_accepted_wrong_history_rows.csv
```

## Result

Artifact:

```text
runs/m1134_row15_promoted_family_aggregate_conversion/summary.json
```

Top-level result:

```text
decision: family_aggregate_conversion_export_pass
passed: true
mixed_source_objective_npz_written: false
training_started: false
ppo_used: false
replay_started: false
objective_optimization_started: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

Aggregate conversion summary:

```text
rows: 172
physical_pairs: 15
left_steps: 6
checkpoints: 5
targets: 3
normal_margin_buckets: 3
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.116279
threshold_pass: true
```

Source distribution:

```text
previous_m1078_base:  7 rows,  4 physical pairs, 3 left steps, 2 targets
row15_current:       28 rows,  5 physical pairs, 4 left steps, 2 targets
short61049:          51 rows, 13 physical pairs, 6 left steps, 3 targets
short61050:          37 rows, 10 physical pairs, 6 left steps, 3 targets
short61051:          49 rows, 13 physical pairs, 6 left steps, 3 targets
```

Duplicate geometry:

```text
duplicate_geometry_groups: 92
duplicate_geometry_multi_source_groups: 0
```

The conversion preserved source labels and wrote replay/audit artifacts only.
It did not create a mixed hidden-state objective corpus.

## Outputs

```text
runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv
runs/m1134_row15_promoted_family_aggregate_conversion/source_policy_map.json
runs/m1134_row15_promoted_family_aggregate_conversion/source_summary.csv
runs/m1134_row15_promoted_family_aggregate_conversion/duplicate_geometry_summary.csv
runs/m1134_row15_promoted_family_aggregate_conversion/replay_plan.json
runs/m1134_row15_promoted_family_aggregate_conversion/summary.json
```

## Interpretation

M1134 confirms that the M1132 fresh promoted-base surface can be exported into a
source-preserving family aggregate replay/audit corpus without losing aggregate
diversity.

This still does not admit training. The replay plan explicitly requires
source-policy-on-source-rows checks, cross-family replay reporting, and duplicate
geometry failure audit before objective optimization.

## Decision

```text
row15_promoted_family_aggregate_conversion_pass_route_to_replay_sanity_design
```

Next:

```text
m1135-v4-public-base-row15-promoted-replay-sanity-design
```
