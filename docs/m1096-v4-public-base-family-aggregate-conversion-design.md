# M1096 V4 Public Base Family-Aggregate Conversion Design

## Purpose

M1096 designs the family-aggregate raw-retained conversion contract selected by
M1094 and M1095.

This milestone is design-only. It does not train, run PPO, run replay, mine
rows, promote a checkpoint, use private holdout, or change actor inputs.

## Why Existing Conversion Is Not Enough

The existing `boundary_outcome_corpus_objective` path intentionally builds one
checkpoint corpus per run:

```text
if len(args.checkpoint_policy) != 1:
    raise ValueError("build exactly one checkpoint corpus per run to avoid mixing hidden-state spaces")
```

That rule is correct for the old per-checkpoint compact corpus design, but it
cannot directly consume the M1092 surface:

```text
proof_current: 16 compact rows / 4 physical pairs
short61049:    17 compact rows / 8 physical pairs
short61050:    13 compact rows / 8 physical pairs
short61051:    29 compact rows / 13 physical pairs
```

M1094 showed that only the raw-retained family aggregate preserves the full
source-balanced surface:

```text
rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.136986
```

Therefore the next conversion path must not pretend that M1092 is a normal
single-checkpoint compact corpus.

## Contract

The family-aggregate conversion contract should first produce a replay/audit
surface, not an objective NPZ.

Required row identity:

```text
family_row_id
source_row_index
source_checkpoint_label
source_checkpoint_path
source_checkpoint_family
physical_pair_key
boundary_geometry_key
duplicate_geometry_group_id
target
left_seed
right_seed
left_step
right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
normal_margin
variant_margin
margin_gap
normal_success
variant_success
success_drop
normal_first_steer
normal_first_throttle
normal_first_brake
variant_first_steer
variant_first_throttle
variant_first_brake
```

Raw retained means:

```text
do not drop rows only because another checkpoint label has the same
boundary_geometry_key
```

Duplicate geometry must be explicit:

```text
duplicate_geometry_group_id = stable group id for boundary_geometry_key
duplicate_geometry_group_size = number of raw retained rows sharing that geometry
duplicate_geometry_source_labels = comma-separated source labels in the group
```

This lets later replay or objective code decide whether duplicates are
evidence from different source policies or redundant rows. M1096 does not
collapse them.

## Source Policy Map

The M1092 family is:

```text
proof_current:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

The implementation must fail closed if a row contains a checkpoint label that
is missing from the source policy map.

## Hidden-State Handling

Do not silently create one mixed hidden-state objective corpus.

The existing single-checkpoint restriction exists because each checkpoint's
online GRU hidden values live in that checkpoint's policy representation. The
architectures are compatible, but the hidden coordinates are not guaranteed to
be semantically aligned after training/projection updates.

M1097 should therefore export metadata and replay-ready rows only. It may
include a design placeholder for future objective arrays, but it must not write
or promote a mixed-source objective NPZ.

Future objective options must be evaluated separately:

```text
Option A: source-specific objective corpora
  Keep one objective corpus per checkpoint label.
  Use aggregate replay as the gate, not aggregate objective training.

Option B: target-base rebuilt hidden states
  Re-collect all selected rows under one target checkpoint before objective
  optimization, so the objective hidden states come from one model.

Option C: mixed-source objective with source-stratified diagnostics
  Only allowed after an explicit audit shows source hidden spaces are compatible
  enough for the objective's claim scope.
```

M1096 recommends Option A or B before any mixed-source objective.

## Replay Sanity Before Objective Optimization

The conversion implementation should not run replay, but it must write a replay
plan that can be executed by the next milestone.

Minimum replay sanity:

```text
source policy -> source rows:
  normal_success_count must not decrease
  wrong_history_success_count must remain 0
  success_drop_count must equal source row count

cross-family policy -> raw retained rows:
  report normal success, wrong-history success, margin gap, and row failures
  do not require pass until a family-intersection criterion is designed

aggregate family replay:
  preserve source labels, duplicate geometry groups, and physical-pair balance
```

Objective optimization is blocked until replay sanity answers whether
raw-retained aggregate rows remain valid under the candidate family.

## Implementation Plan

M1097 should implement:

```text
src/autodrift/family_aggregate_boundary_conversion.py
tests/test_family_aggregate_boundary_conversion.py
```

Inputs:

```text
--accepted-rows-csv runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
--source-policy-map-json <json path or inline map>
--run-dir runs/m1097_family_aggregate_boundary_conversion
```

Outputs:

```text
family_aggregate_boundary_rows.csv
source_policy_map.json
source_summary.csv
duplicate_geometry_summary.csv
replay_plan.json
summary.json
```

Implementation gates:

```text
rows >= 80
physical_pairs >= 10
left_steps >= 5
checkpoints >= 3
targets >= 2
normal_margin_buckets >= 2
success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
all source_checkpoint_label values are mapped
no training / PPO / replay / mining / promotion / private holdout
```

## Next Milestone

```text
m1097-v4-public-base-family-aggregate-conversion-implementation
```

M1097 should implement and run the export-only conversion contract. It should
not run replay or objective optimization. If the export fails any of the gates,
route back to design or synthesis rather than weakening M1092 thresholds.

## Self-ID Claim Level

M1096 keeps the branch at:

```text
level2_history_encoded_reactive
```

It is a conversion design for matched-current wrong-history rows. It does not
add a pre-emergency temporal window or support level-3 anticipatory
self-identification.

## Validation

Research validation:

```text
make research-validate
```

Result before commit:

```text
research validation passed
process_v5_from_priority=10850
```

Harness tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py \
  tests/test_source_balanced_compactability_audit.py
```

Result:

```text
38 passed
```

Git hook:

```text
.git/hooks/pre-commit
```

Result:

```text
19 passed
```

## Decision

```text
family_aggregate_conversion_design_admit_export_implementation
```
