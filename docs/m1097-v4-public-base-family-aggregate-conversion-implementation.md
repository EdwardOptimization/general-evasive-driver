# M1097 V4 Public Base Family-Aggregate Conversion Implementation

## Purpose

M1097 implements and runs the export-only family-aggregate raw-retained
conversion contract designed in M1096.

This milestone does not train, run PPO, run replay, run objective optimization,
mine rows, promote a checkpoint, use private holdout, or change actor inputs.

## Implementation

Added:

```text
src/autodrift/family_aggregate_boundary_conversion.py
tests/test_family_aggregate_boundary_conversion.py
```

The exporter:

1. reads the M1092 accepted wrong-history rows;
2. keeps raw retained rows without dropping duplicate geometry;
3. requires every `checkpoint_label` to be present in the source policy map;
4. writes source checkpoint label/path metadata per row;
5. writes duplicate geometry group metadata;
6. writes a replay plan;
7. refuses to write a mixed-source objective NPZ.

## Command

```text
PYTHONPATH=src python -m autodrift.family_aggregate_boundary_conversion \
  --accepted-rows-csv runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv \
  --source-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --source-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --source-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --source-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --run-dir runs/m1097_family_aggregate_boundary_conversion
```

## Artifacts

```text
runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv
runs/m1097_family_aggregate_boundary_conversion/source_policy_map.json
runs/m1097_family_aggregate_boundary_conversion/source_summary.csv
runs/m1097_family_aggregate_boundary_conversion/duplicate_geometry_summary.csv
runs/m1097_family_aggregate_boundary_conversion/replay_plan.json
runs/m1097_family_aggregate_boundary_conversion/summary.json
```

## Results

Aggregate export:

```text
rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
normal_margin_buckets: 4
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.1369863014
threshold_pass: true
```

Source summary:

```text
proof_current:
  rows: 39
  physical_pairs: 4
  left_steps: 3
  targets: 2

short61049:
  rows: 29
  physical_pairs: 8
  left_steps: 5
  targets: 2

short61050:
  rows: 24
  physical_pairs: 8
  left_steps: 6
  targets: 3

short61051:
  rows: 54
  physical_pairs: 13
  left_steps: 8
  targets: 3
```

Duplicate geometry:

```text
duplicate_geometry_groups: 75
duplicate_geometry_multi_source_groups: 0
```

The zero multi-source duplicate groups mean the raw-retained row surplus is
mostly within-source repeated geometry variants, not identical geometry shared
across checkpoint labels. That does not invalidate the aggregate export, but
the replay sanity design should audit repeated same-source geometry groups.

Safety flags:

```text
training_started: false
ppo_used: false
replay_started: false
objective_optimization_started: false
mixed_source_objective_npz_written: false
mining_started: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

## Replay Plan

`replay_plan.json` requires future checks:

```text
source_policy_on_source_rows_normal_success_retention
source_policy_on_source_rows_wrong_history_failure_retention
cross_family_replay_report_before_objective_optimization
duplicate_geometry_group_failure_audit
```

It also explicitly records:

```text
replay_started: false
objective_optimization_started: false
mixed_source_objective_npz_allowed: false
promotion_allowed: false
```

## Decision

```text
family_aggregate_conversion_export_pass
```

Next:

```text
m1098-v4-public-base-family-aggregate-replay-sanity-design
```

M1098 should design the replay sanity step before any objective optimization.
It should define source-policy-on-source-rows gates, cross-family replay
reports, duplicate geometry audits, and failure taxonomy without running replay
inside the design milestone.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_aggregate_boundary_conversion.py
```

Result:

```text
5 passed
```

Harness tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_aggregate_boundary_conversion.py \
  tests/test_source_balanced_compactability_audit.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

Result:

```text
43 passed
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
