# M1140 V4 Public Base Row15 Promoted Target Materialization Design

## Purpose

M1140 designs target-policy materialization for the M1139 all-policy
intersection rows under the current public-gate base.

This milestone is design-only. It does not run replay, optimize an objective,
train actor weights, run PPO, mine rows, promote a checkpoint, use private
holdout, write an objective NPZ, or change actor inputs.

## Problem

M1139 produced a family-intersection surface:

```text
kept rows: 148
physical pairs: 13
source labels: 5
targets: 2
left steps: 6
```

The rows pass under all five family policies, but
`family_intersection_rows.csv` must not be fed directly into an objective
corpus.

Reason:

```text
family_intersection_rows.csv preserves source-policy rows and source-row
margins/actions, while the next objective should optimize one target policy.
```

The objective corpus should use one hidden-state/action/margin space. Otherwise
the loss would mix source-policy hidden states with current-base target-policy
actions and margins.

## Target Policy

The first materialization target should be:

```text
target_policy_label: row15_current
target_policy_path:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

This is the current public-gate base promoted in M1129. Other source policies
remain provenance and diversity labels only.

## Inputs

Required inputs:

```text
runs/m1139_row15_promoted_intersection_selector/family_intersection_rows.csv
runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv
```

The materialization implementation must not call replay. It should use the
existing M1136 replay rows and join only the `row15_current` policy rows for
target objective fields.

## Join Rule

For each selected `family_row_id`:

1. find the replay row where `policy == row15_current`;
2. fail closed if the replay row is missing;
3. fail closed if it does not satisfy:

```text
normal_success == true
wrong_history_success == false
success_drop == true
finite normal_margin
finite wrong_history_margin
finite margin_gap
```

M1139 already checked this across all five policies, but materialization must be
self-contained so that future objective conversion cannot silently accept a bad
join.

## Field Mapping

Use target-policy replay fields for objective semantics:

```text
checkpoint_label            <- row15_current
target_policy_label         <- row15_current
target_policy_checkpoint    <- replay.checkpoint
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

Use the intersection/source row for geometry and provenance:

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

Preserve original source-row values under diagnostic prefixes, for example:

```text
source_normal_margin
source_variant_margin
source_margin_gap
source_normal_success
source_variant_success
source_success_drop
```

These prefixed fields must not be used as objective labels for the target
policy.

## M1142 Candidate Command

Because the `row15_promoted_base_surface_refresh` branch has reached the
10-milestone synthesis cadence, M1141 should synthesize the branch before this
command runs. If M1141 decides to continue, the materialization run should use:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.family_intersection_target_policy_materialization \
  --family-intersection-rows-csv runs/m1139_row15_promoted_intersection_selector/family_intersection_rows.csv \
  --cross-family-replay-rows-csv runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv \
  --target-policy-label row15_current \
  --run-dir runs/m1142_row15_promoted_target_materialization \
  --expected-rows 148 \
  --min-physical-pairs 12 \
  --min-source-labels 4 \
  --min-targets 2 \
  --min-left-steps 6 \
  --max-physical-pair-fraction 0.25 \
  --max-source-label-fraction 0.45
```

## Output Contract

If admitted after synthesis, the materializer should write:

```text
runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
runs/m1142_row15_promoted_target_materialization/row15_current_source_summary.csv
runs/m1142_row15_promoted_target_materialization/row15_current_target_summary.csv
runs/m1142_row15_promoted_target_materialization/row15_current_materialization_summary.json
```

No objective NPZ should be written during materialization. Objective corpus
construction remains a separate milestone after materialized rows pass
validation.

## Validation Gate

Materialization should pass only if:

```text
rows == 148
normal_success_count == 148
wrong_history_success_count == 0
success_drop_count == 148
finite objective rows == 148
physical_pairs >= 12
source_labels >= 4
targets >= 2
left_steps >= 6
max_physical_pair_fraction <= 0.25
max_source_label_fraction <= 0.45
```

The output must pass `validate_boundary_row_frame(materialized_rows)`.

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

## Workflow Cadence

M1131 through M1140 complete the 10-milestone cadence for the
`row15_promoted_base_surface_refresh` branch:

```text
M1131 design refresh
M1132 run refresh
M1133 design conversion
M1134 run conversion
M1135 design replay sanity
M1136 run replay sanity
M1137 audit cross-family replay
M1138 design selector
M1139 run selector
M1140 design materialization
```

Therefore the next step should be a synthesis milestone before any
implementation or objective conversion.

## Decision

```text
row15_promoted_target_materialization_design_route_to_branch_synthesis
```

Next:

```text
m1141-v4-public-base-row15-promoted-surface-refresh-synthesis
```
