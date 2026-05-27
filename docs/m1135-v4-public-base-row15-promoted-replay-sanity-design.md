# M1135 V4 Public Base Row15 Promoted Replay Sanity Design

## Purpose

M1135 designs source-aware replay sanity for the M1134 source-preserving family
aggregate rows before any objective conversion or training.

This milestone is design-only. It does not run replay, optimize an objective,
train actor weights, run PPO, promote, use private holdout, or change actor
inputs.

## Inputs

```text
runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv
runs/m1134_row15_promoted_family_aggregate_conversion/source_policy_map.json
runs/m1134_row15_promoted_family_aggregate_conversion/replay_plan.json
```

M1134 export:

```text
rows: 172
physical_pairs: 15
left_steps: 6
checkpoints: 5
targets: 3
duplicate_geometry_groups: 92
duplicate_geometry_multi_source_groups: 0
```

## M1136 Command

Run the existing source-aware replay wrapper:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.family_aggregate_replay_sanity \
  --family-rows-csv runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-rows 0 \
  --max-continuation-steps 60 \
  --device cpu \
  --run-dir runs/m1136_row15_promoted_family_aggregate_replay_sanity
```

## Source-Policy Source-Rows Gate

For each source label, evaluate that source policy on only its own exported
rows.

Required:

```text
normal_success_count == source_row_count
wrong_history_success_count == 0
success_drop_count == source_row_count
gate_pass == true
```

Aggregate source gate:

```text
source_row_count == 172
normal_success_count == 172
wrong_history_success_count == 0
success_drop_count == 172
physical_pairs >= 12
checkpoints >= 4
targets >= 2
gate_pass == true
```

If the source-policy gate fails, do not continue toward objective conversion.
Classify as `proof_washout` if replay genuinely loses the normal/wrong-history
relation, or `metric_artifact` if metadata/replay row identity is wrong.

## Cross-Family Replay Report

M1136 should also replay each policy on all rows, but this is a diagnostic
report rather than a promotion gate.

Required outputs:

```text
cross_family_replay_rows.csv
cross_family_policy_summary.csv
duplicate_geometry_replay_summary.csv
failed_duplicate_geometry_groups.csv
```

The cross-family report decides whether the next step should be:

```text
family-intersection replay-calibrated rows
source-specific objective corpora
target-base rebuilt hidden-state rows
```

## Duplicate Geometry Audit

Failures must be grouped by:

```text
duplicate_geometry_group_id
physical_pair_key
target
source_checkpoint_label
```

This prevents repeated geometry variants from making a pass or failure look
larger than it is.

## Outputs

M1136 should write:

```text
source_policy_source_rows_replay.csv
source_policy_gate_summary.csv
cross_family_replay_rows.csv
cross_family_policy_summary.csv
duplicate_geometry_replay_summary.csv
failed_duplicate_geometry_groups.csv
summary.json
```

## Decision

```text
row15_promoted_replay_sanity_design_admit_m1136_run
```

Next:

```text
m1136-v4-public-base-row15-promoted-replay-sanity
```
