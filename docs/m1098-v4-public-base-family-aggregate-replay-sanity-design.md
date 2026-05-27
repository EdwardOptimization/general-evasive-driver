# M1098 V4 Public Base Family-Aggregate Replay Sanity Design

## Purpose

M1098 designs replay sanity for the M1097 family-aggregate raw-retained export
before objective optimization.

This milestone is design-only. It does not train, run PPO, run replay, run
objective optimization, mine rows, promote a checkpoint, use private holdout,
or change actor inputs.

## Input

Use:

```text
runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv
runs/m1097_family_aggregate_boundary_conversion/source_policy_map.json
runs/m1097_family_aggregate_boundary_conversion/replay_plan.json
```

M1097 export:

```text
rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
duplicate_geometry_groups: 75
duplicate_geometry_multi_source_groups: 0
```

## Existing Replay Tooling

`boundary_outcome_replay_gate` already has the low-level replay function needed
for normal-history and wrong-history rollout:

```text
replay_boundary_rows_for_policy(...)
```

It expects replay rows with:

```text
row_id
target
physical_pair_key
left_seed
right_seed
left_step
right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
```

M1097 rows contain the required geometry fields, but use `family_row_id`
instead of `row_id` and include additional metadata:

```text
source_checkpoint_label
source_checkpoint_path
duplicate_geometry_group_id
duplicate_geometry_group_size
duplicate_geometry_source_labels
```

Therefore M1099 should implement a source-aware wrapper, not modify the core
replay function.

## Replay Wrapper Contract

M1099 should implement:

```text
src/autodrift/family_aggregate_replay_sanity.py
tests/test_family_aggregate_replay_sanity.py
```

The wrapper should:

1. read `family_aggregate_boundary_rows.csv`;
2. create replay rows with `row_id = family_row_id`;
3. run `replay_boundary_rows_for_policy` for each requested checkpoint policy;
4. join replay results back to source metadata on `row_id`;
5. write raw replay rows, source-policy source-row gates, cross-family report,
   duplicate geometry report, and summary JSON.

It must preserve:

```text
family_row_id
source_checkpoint_label
source_checkpoint_path
physical_pair_key
boundary_geometry_key
duplicate_geometry_group_id
target
```

## Gate Tiers

### Source-Policy Source-Rows Gate

For each source label, evaluate that source policy on only its own exported
rows.

Required gates:

```text
normal_success_count == source_row_count
wrong_history_success_count == 0
success_drop_count == source_row_count
finite_margin_gap_fraction == 1.0
```

This is the first proof that the exported rows still reproduce the accepted
M1092 relation after conversion.

### Aggregate Source Gate

Across all source-policy source-row replays:

```text
rows == 146
normal_success_rate == 1.0
wrong_history_success_rate == 0.0
success_drop_rate == 1.0
physical_pairs >= 10
checkpoints >= 3
targets >= 2
```

If this fails, do not run objective optimization. Classify the failure as:

```text
metric_artifact
```

if the failure is from export/replay metadata mismatch, or:

```text
proof_washout
```

if replay shows the rows no longer express the intended normal/wrong-history
relation under their source policies.

### Cross-Family Replay Report

For each policy, also replay all rows. This is a report, not an immediate
promotion gate.

Metrics:

```text
policy
source_checkpoint_label
target
rows
normal_success_rate
wrong_history_success_rate
success_drop_count
normal_margin_mean
wrong_history_margin_mean
margin_gap_mean
margin_gap_min
failed_family_row_ids
```

The goal is to decide whether the next branch should build:

```text
family-intersection replay-calibrated rows
```

or:

```text
source-specific objective corpora
```

### Duplicate Geometry Failure Audit

Replay failures should be grouped by:

```text
duplicate_geometry_group_id
physical_pair_key
target
source_checkpoint_label
```

Required outputs:

```text
duplicate_geometry_replay_summary.csv
failed_duplicate_geometry_groups.csv
```

This prevents repeated same-source geometry variants from dominating a pass or
failure interpretation.

## Outputs

M1099 should write:

```text
source_policy_source_rows_replay.csv
source_policy_gate_summary.csv
cross_family_replay_rows.csv
cross_family_policy_summary.csv
duplicate_geometry_replay_summary.csv
failed_duplicate_geometry_groups.csv
summary.json
```

## Decision Rule

M1099 may pass only if:

```text
source-policy source-rows gate passes for every source label
aggregate source gate passes
all row/source/duplicate metadata is preserved
no replay uses private holdout
no objective optimization starts
no checkpoint is promoted
```

If source-policy source-rows pass but cross-family report shows many failures,
that is not a blocker for the export. It routes to family-intersection design.

If source-policy source-rows fail, the conversion is not admissible for
objective optimization; route to export repair or source-specific conversion.

## Next Milestone

```text
m1099-v4-public-base-family-aggregate-replay-sanity-implementation
```

M1099 should implement and run the source-aware replay sanity wrapper. It may
run replay, because this M1098 design will pre-register the replay gates.
M1099 still must not train, run PPO, run objective optimization, mine rows,
promote, use private holdout, or change actor inputs.

## Self-ID Claim Level

M1098 remains:

```text
level2_history_encoded_reactive
```

Replay sanity over matched-current rows does not create a level-3 anticipatory
self-identification claim.

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
family_aggregate_replay_sanity_design_admit_wrapper_run
```
