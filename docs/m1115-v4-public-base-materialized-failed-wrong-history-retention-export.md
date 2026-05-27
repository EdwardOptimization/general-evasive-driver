# M1115 V4 Public Base Materialized Failed Wrong-History Retention Export

## Purpose

M1115 implements and runs the failed wrong-history retention export designed in
M1114.

This milestone is infrastructure-only. It does not train actor weights, run PPO,
run replay gates, mine new rows, promote a checkpoint, use private holdout, or
change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_failed_wrong_history_retention_export \
  --base-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --full-gate-run-dir runs/m1112_materialized_actor_update_full_public_gate \
  --base-combined-anchor-npz runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --failed-row-weight 50 \
  --target-source-index-offset 2000000 \
  --device cpu \
  --run-dir runs/m1115_materialized_failed_wrong_history_retention_export
```

## Result

The export passes:

```text
result_class: materialized_failed_wrong_history_retention_export_pass
failed_event_count: 47
normal_lost_events: 0
wrong_history_safe_events: 47
target_base_failed_events: 19
family_source_failed_events: 28
target_anchor_rows: 707
combined_anchor_rows: 4664
short_family_rows_in_training_anchor: false
```

The failed-row registry exactly reproduces the M1113 diagnosis: every lost
success-drop event is caused by the candidate making wrong-history branches safe,
not by losing normal-history success.

## Surface Split

Target-base rows are eligible for trajectory-anchor export because they can be
reconstructed in the current public-base hidden-state space:

```text
old_public:
  m183_m168: 1
  m223_m219: 1
  m267_m264: 6

source_diverse:
  current_m333_surface: 3
  m314_continuity_surface: 4
  m317_continuity_surface: 4
```

Family-source rows are not used as training anchors:

```text
family_intersection:
  short61049_to_m964_direction_target_a0_15: 8
  short61050_to_m964_direction_target_a0_15: 10
  short61051_to_m964_direction_target_a0_15: 10
```

Those rows remain mandatory replay diagnostics until a target-policy
materialization step is explicitly designed.

## Artifacts

Primary artifacts:

```text
runs/m1115_materialized_failed_wrong_history_retention_export/summary.json
runs/m1115_materialized_failed_wrong_history_retention_export/failed_wrong_history_events.csv
runs/m1115_materialized_failed_wrong_history_retention_export/target_base_failed_rows.csv
runs/m1115_materialized_failed_wrong_history_retention_export/family_source_failed_rows.csv
runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.npz
runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.csv
runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz
runs/m1115_materialized_failed_wrong_history_retention_export/surface_failure_summary.csv
```

Anchor sanity:

```text
target_base_rejected_trajectory_anchor.npz:
  observation: [707, 72]
  hidden: [707, 128]
  reference_action: [707, 3]
  source_index: 0..18
  raw weight sum: 35350.0

combined_target_base_rejected_anchor.npz:
  rows: 4664
  source namespace: 0..2000018, no collision
  family 0 weight sum: 1.0
  family 1 weight sum: 4.0
  family 2 weight sum: 4.0
```

The combined anchor appends the new target-base rejected-history family with a
separate source namespace and normalized family total. It preserves the existing
base anchor family metadata.

## Interpretation

M1115 makes the M1113 failure actionable. The project now has:

- a deterministic registry of the exact 47 M1112 proof-washout events;
- a clean split between target-base rows and short-family rows;
- a loadable target-base rejected-history trajectory anchor;
- a loadable combined active-set plus target-base rejected-history anchor;
- an explicit guarantee that short-family hidden states are not included in the
  training anchor.

This is not driver improvement evidence. It is the infrastructure needed before
the next actor-update design can test whether rejected-history trajectory
retention prevents M1112-style proof washout.

## Decision

```text
materialized_failed_wrong_history_retention_export_pass_route_to_actor_update_design
```

Next milestone:

```text
m1116-v4-public-base-failed-wrong-history-retention-actor-update-design
```
