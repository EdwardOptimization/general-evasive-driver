# M1114 V4 Public Base Materialized Failed Wrong-History Retention Design

## Purpose

M1114 designs the next repair path after M1113 proved that M1112 failed because
wrong-history branches became safe.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, export a corpus, mine rows, promote a checkpoint, use private holdout,
retry backup candidates, or change actor inputs.

## Parent Failure

M1113 found:

```text
lost_success_drop_events: 47
normal_lost_events: 0
wrong_history_safe_events: 47
```

Therefore the missing constraint is not normal-history recovery. The missing
constraint is closed-loop rejected-history retention.

## Design Principle

Do not directly anchor hidden states from another checkpoint family into the
current public-base actor.

This matters because M1112 failures come from three tiers:

```text
old public replay:
  baseline policy is the current public-gate base / m399_base lineage

source-diverse replay:
  baseline policy is the current public-gate base / m399_base lineage

family-intersection replay:
  baseline policies are short61049, short61050, short61051
```

The old public and source-diverse rows can be exported in the current public
base hidden-state space. The short-family rows need target-policy
materialization or must remain replay-only diagnostics. They should not be
converted into training anchors using short-policy hidden states.

## M1115 Export Contract

M1115 should implement a no-training export tool:

```text
autodrift.materialized_failed_wrong_history_retention_export
```

Inputs:

```text
base checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

M1112 full gate run:
  runs/m1112_materialized_actor_update_full_public_gate

env config:
  configs/m121_human_view_zero_obstacle_relvel.json

existing base combined anchor:
  runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

Primary output directory:

```text
runs/m1115_materialized_failed_wrong_history_retention_export
```

Required outputs:

```text
failed_wrong_history_events.csv
target_base_failed_rows.csv
family_source_failed_rows.csv
target_base_rejected_trajectory_anchor.npz
target_base_rejected_trajectory_anchor.csv
combined_target_base_rejected_anchor.npz
summary.json
```

## Failed-Row Registry

The registry must include one row per lost success-drop event with at least:

```text
surface_label
surface_tier
corpus_csv
row_id
target
physical_pair_key
baseline_policy
candidate_policy
normal_lost
wrong_history_safe
base_wrong_history_margin
candidate_wrong_history_margin
base_margin_gap
candidate_margin_gap
left_seed
right_seed
left_step
right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
```

The expected registry count from M1113 is:

```text
failed_wrong_history_events: 47
normal_lost_events: 0
wrong_history_safe_events: 47
```

If these counts do not reproduce, M1115 should fail closed.

## Target-Base Split

M1115 must split failed rows:

```text
target_base_failed_rows:
  old public failed rows
  source-diverse failed rows
  any row whose baseline policy is the current public-gate base lineage

family_source_failed_rows:
  short61049 failed rows
  short61050 failed rows
  short61051 failed rows
```

The target-base rows may be used for a trajectory anchor because the reference
hidden states and actions can be reconstructed in the current base's hidden
state space.

The family-source rows must not be used as trajectory anchors until they are
materialized into the current base hidden-state space. They remain replay
diagnostics for the next gate.

## Trajectory Anchor Schema

For each target-base failed row, M1115 should reconstruct the current-base left
snapshot, relocate the obstacle to the failed boundary geometry, start from the
matched current-base wrong-history hidden state, and record the current-base
wrong-history action trajectory.

The exported NPZ must be compatible with `load_trajectory_action_anchor`:

```text
observation: float32 [N, 72]
hidden: float32 [N, 128]
reference_action: float32 [N, 3]
source_index: int64 [N]
step_index: int64 [N]
weight: float32 [N]
```

Required weighting:

```text
base row weight: 10
failed-row weight: 50
source-family normalization: enabled
source_index namespacing: enabled
```

The combined anchor should append target-base rejected trajectories to:

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

The combined anchor should use source offsets so M293/M1034 and M1115 sources
do not collide.

## Gate Order After Export

If M1115 succeeds, the next actor-update design must gate in this order:

```text
1. anchor load and shape sanity;
2. exact M1107 objective no-regression;
3. target-base failed-row trajectory-anchor loss no-regression;
4. allowed parameter surface;
5. old public first replay;
6. source-diverse first replay;
7. family-intersection replay remains mandatory but may not be trained from
   short-policy hidden states unless materialized;
8. behavior seeds;
9. no PPO and no promotion.
```

## Rejected Shortcuts

Do not:

```text
retry m1110_110900 or m1110_110902;
increase M1107 objective weight;
run a longer actor update;
use short61049/short61050/short61051 hidden states as training anchors;
weaken replay gates;
promote or run PPO;
use private holdout.
```

## Decision

```text
materialized_failed_wrong_history_retention_design_admit_export
```

Next milestone:

```text
m1115-v4-public-base-materialized-failed-wrong-history-retention-export
```
