# M1099 V4 Public Base Family-Aggregate Replay Sanity Implementation

## Purpose

M1099 implements and runs the source-aware replay sanity wrapper designed in
M1098.

This milestone runs replay only. It does not train, run PPO, run objective
optimization, mine rows, promote a checkpoint, use private holdout, or change
actor inputs.

## Implementation

Added:

```text
src/autodrift/family_aggregate_replay_sanity.py
tests/test_family_aggregate_replay_sanity.py
```

The wrapper:

1. reads `family_aggregate_boundary_rows.csv`;
2. maps `row_id = family_row_id` for the existing replay function;
3. runs replay for all requested checkpoint policies;
4. joins `source_checkpoint_label`, source path, and duplicate geometry
   metadata back onto replay rows;
5. writes source-policy source-row gates, cross-family reports, duplicate
   geometry reports, and summary JSON.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.family_aggregate_replay_sanity \
  --family-rows-csv runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --run-dir runs/m1099_family_aggregate_replay_sanity \
  --device cpu
```

## Artifacts

```text
runs/m1099_family_aggregate_replay_sanity/source_policy_source_rows_replay.csv
runs/m1099_family_aggregate_replay_sanity/source_policy_gate_summary.csv
runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv
runs/m1099_family_aggregate_replay_sanity/cross_family_policy_summary.csv
runs/m1099_family_aggregate_replay_sanity/duplicate_geometry_replay_summary.csv
runs/m1099_family_aggregate_replay_sanity/failed_duplicate_geometry_groups.csv
runs/m1099_family_aggregate_replay_sanity/summary.json
```

## Source-Policy Gate

Source-policy source-row replay passes for every source label:

```text
proof_current:
  rows: 39
  normal_success_count: 39
  wrong_history_success_count: 0
  success_drop_count: 39
  gate_pass: true

short61049:
  rows: 29
  normal_success_count: 29
  wrong_history_success_count: 0
  success_drop_count: 29
  gate_pass: true

short61050:
  rows: 24
  normal_success_count: 24
  wrong_history_success_count: 0
  success_drop_count: 24
  gate_pass: true

short61051:
  rows: 54
  normal_success_count: 54
  wrong_history_success_count: 0
  success_drop_count: 54
  gate_pass: true
```

Aggregate source gate:

```text
source_row_count: 146
source_replay_row_count: 146
normal_success_count: 146
wrong_history_success_count: 0
success_drop_count: 146
physical_pairs: 18
checkpoints: 4
targets: 3
gate_pass: true
```

This verifies that the M1097 export preserves the intended source-policy
normal-history success and wrong-history failure relation.

## Cross-Family Report

Cross-family replay writes:

```text
replay_rows: 584
cross_family_summary_rows: 40
duplicate_geometry_summary_rows: 300
failed_duplicate_geometry_groups: 14
```

The failures are cross-family report failures, not source-policy source-row
gate failures. Examples:

```text
proof_current on short61050 braking rows:
  normal_success_rate: 0.647059
  failed rows: 140..145

proof_current on short61051 yaw rows:
  wrong_history_success_rate: 0.121212
  failed rows: 135..138

short61050 on short61051 braking rows:
  wrong_history_success_rate: 0.052632
  failed row: 30
```

This means the family-aggregate export is valid as source-policy proof, but a
cross-family objective still needs another decision. Do not proceed directly to
objective optimization.

## Decision

```text
family_aggregate_replay_sanity_source_gate_pass_route_to_cross_family_audit
```

Next:

```text
m1100-v4-public-base-family-aggregate-cross-family-replay-audit
```

M1100 should audit the cross-family report and choose between:

```text
family-intersection replay-calibrated rows
source-specific objective corpora
target-base rebuilt hidden-state rows
```

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_aggregate_replay_sanity.py
```

Result:

```text
5 passed
```

Harness tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_aggregate_replay_sanity.py \
  tests/test_family_aggregate_boundary_conversion.py \
  tests/test_source_balanced_compactability_audit.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

Result:

```text
48 passed
```

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
process_v5_from_priority=10850
```

Git hook:

```text
.git/hooks/pre-commit
```

Result:

```text
19 passed
```
