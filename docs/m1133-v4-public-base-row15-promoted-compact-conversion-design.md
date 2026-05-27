# M1133 V4 Public Base Row15 Promoted Compact Conversion Design

## Purpose

M1133 designs compact, source-preserving conversion from the M1132 promoted-base
source-balanced surface.

This milestone is design-only. It does not run conversion, replay, objective
optimization, actor training, PPO, promotion, private holdout, or actor-input
changes.

## Input Surface

Use the M1132 balanced accepted wrong-history rows:

```text
runs/m1132_row15_promoted_source_balanced_surface_seed113200/balanced_accepted_wrong_history_rows.csv
```

M1132 surface quality:

```text
accepted_wrong_rows: 172
accepted_wrong_physical_pairs: 15
accepted_wrong_left_steps: 6
accepted_wrong_checkpoints: 5
accepted_wrong_targets: 3
accepted_wrong_normal_margin_buckets: 3
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.116279
control_accepted_wrong_rows: 0
```

## Conversion Approach

M1134 should first run export-only family-aggregate conversion. It should not
write a mixed hidden-state objective NPZ and should not train.

The conversion must preserve:

```text
source_checkpoint_label
source_checkpoint_path
source_checkpoint_family
physical_pair_key
boundary_geometry_key
duplicate_geometry_group_id
duplicate_geometry_group_size
duplicate_geometry_source_labels
target
normal/variant margins
normal/variant first actions
success_drop
```

The family-aggregate rows are replay/audit artifacts. Objective optimization
remains blocked until replay sanity and target-policy materialization are
explicitly designed.

## Source Policy Map

```text
row15_current:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

previous_m1078_base:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

The conversion must fail closed if any row has an unmapped checkpoint label.

## M1134 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.family_aggregate_boundary_conversion \
  --accepted-rows-csv runs/m1132_row15_promoted_source_balanced_surface_seed113200/balanced_accepted_wrong_history_rows.csv \
  --source-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --source-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --source-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --source-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --source-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --source-family row15_promoted_family \
  --min-margin-gap 0.0 \
  --margin-bucket-width 0.005 \
  --min-rows 100 \
  --min-physical-pairs 12 \
  --min-left-steps 6 \
  --min-checkpoints 4 \
  --min-targets 2 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-physical-pair-fraction 0.25 \
  --run-dir runs/m1134_row15_promoted_family_aggregate_conversion
```

## M1134 Acceptance Criteria

Conversion passes only if:

```text
rows >= 100
physical_pairs >= 12
left_steps >= 6
checkpoints >= 4
targets >= 2
normal_margin_buckets >= 2 at width 0.005
success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
all source_checkpoint_label values are mapped
family_aggregate_boundary_rows.csv exists
source_policy_map.json exists
source_summary.csv exists
duplicate_geometry_summary.csv exists
replay_plan.json exists
summary.json exists
training_started == false
ppo_used == false
replay_started == false
objective_optimization_started == false
promoted == false
private_holdout_used == false
```

## Next If M1134 Passes

Do not train from the aggregate rows directly. The next step after a conversion
pass should be source-aware replay sanity design:

```text
source policy -> source rows:
  normal success retained
  wrong-history success remains zero
  success-drop count equals source row count

current public base -> aggregate rows:
  source-diverse proof behavior reported before objective conversion
```

Only after replay sanity should the project decide whether to materialize rows
under the current base for single-checkpoint objective optimization.

## Decision

```text
row15_promoted_compact_conversion_design_admit_m1134_export
```

Next:

```text
m1134-v4-public-base-row15-promoted-family-aggregate-conversion
```
