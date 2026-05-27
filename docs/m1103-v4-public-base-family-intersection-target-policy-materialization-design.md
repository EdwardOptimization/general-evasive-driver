# M1103 V4 Public Base Family-Intersection Target-Policy Materialization Design

## Purpose

M1103 designs how M1102 all-policy intersection rows become objective-ready
boundary rows for one target policy.

This milestone is design-only. It does not train, run PPO, run replay, run
objective optimization, mine rows, promote a checkpoint, use private holdout, or
change actor inputs.

## Problem

M1102 produces a valid all-policy intersection:

```text
kept rows: 133
physical pairs: 14
source labels: 4
targets: 3
left steps: 9
```

But `family_intersection_rows.csv` must not be fed directly into
`boundary_outcome_corpus_objective`.

Reason:

```text
family_intersection_rows.csv still contains source checkpoint labels and
source-row margins/actions.
```

The existing boundary-outcome objective intentionally builds exactly one
checkpoint corpus per run to avoid hidden-state-space mixing. If we optimize the
current public-gate base, the objective rows must use that target policy's
replay-calibrated margins/actions and later collect hidden states from that same
target policy.

## Target Policy

The first materialization target should be:

```text
target_policy_label: proof_current
target_policy_path:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

This is the current public-gate proof base. Other family policies may be
materialized later, but each run should emit rows for one target policy only.

## Inputs

Required inputs:

```text
runs/m1102_family_aggregate_intersection_selector/family_intersection_rows.csv
runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv
```

The implementation must not call replay. It should use the existing M1099 replay
metrics.

## Join Rule

For each kept `family_row_id`:

1. find the replay row where `policy == target_policy_label`;
2. fail closed if it is missing;
3. fail closed if it does not satisfy:

```text
normal_success == true
wrong_history_success == false
success_drop == true
finite normal_margin
finite wrong_history_margin
finite margin_gap
```

The selector has already checked this across all policies, but materialization
must be self-contained.

## Field Mapping

Materialized rows should satisfy
`boundary_outcome_corpus_objective.REQUIRED_BOUNDARY_ROW_COLUMNS`.

Use target-policy replay fields for objective semantics:

```text
checkpoint_label            <- target_policy_label
normal_margin               <- replay.normal_margin
variant_margin              <- replay.wrong_history_margin
margin_gap                  <- replay.margin_gap
normal_success              <- replay.normal_success
variant_success             <- replay.wrong_history_success
success_drop                <- replay.success_drop
normal_first_steer          <- replay.normal_first_steer
normal_first_throttle       <- replay.normal_first_throttle
normal_first_brake          <- replay.normal_first_brake
variant_first_steer         <- replay.wrong_history_first_steer
variant_first_throttle      <- replay.wrong_history_first_throttle
variant_first_brake         <- replay.wrong_history_first_brake
variant                     <- wrong_matched_history
accepted                    <- true
```

Use intersection/source rows for geometry and provenance:

```text
family_row_id
source_row_index
source_checkpoint_label
source_checkpoint_path
source_checkpoint_family
physical_pair_key
boundary_geometry_key
duplicate_geometry_group_id
duplicate_geometry_group_size
duplicate_geometry_source_labels
target
left_seed/right_seed
left_step/right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
```

Preserve original source-row scores under prefixed diagnostic fields, for
example:

```text
source_normal_margin
source_variant_margin
source_margin_gap
source_normal_success
source_variant_success
source_success_drop
```

Those prefixed source fields are not objective labels.

## Output Contract

The implementation should write:

```text
runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv
runs/m1104_target_policy_materialization/proof_current_source_summary.csv
runs/m1104_target_policy_materialization/proof_current_target_summary.csv
runs/m1104_target_policy_materialization/proof_current_materialization_summary.json
```

No NPZ should be written in M1104. Objective corpus construction remains a
separate milestone after the materialized rows pass validation.

## Validation Gate

Materialization passes only if:

```text
rows == 133
normal_success_count == 133
wrong_history_success_count == 0
success_drop_count == 133
finite objective margin rows == 133
physical_pairs >= 10
source_labels >= 4
targets >= 3
left_steps >= 8
max_physical_pair_fraction <= 0.20
max_source_label_fraction <= 0.45
```

The materialized output must pass
`validate_boundary_row_frame(materialized_rows)`.

## Safety

The materializer must not:

```text
train
run PPO
run replay
run objective optimization
mine rows
write objective NPZ
promote a checkpoint
use private holdout
change actor inputs
mix multiple target policies into one boundary-row file
```

## Decision

```text
target_policy_materialization_design_admit_implementation
```

Next:

```text
m1104-v4-public-base-family-intersection-target-policy-materialization-implementation
```

M1104 should implement the materializer and run it for `proof_current` only. If
validation fails, route to source-specific corpora design or artifact repair
instead of weakening the hidden-state-space separation rule.

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
