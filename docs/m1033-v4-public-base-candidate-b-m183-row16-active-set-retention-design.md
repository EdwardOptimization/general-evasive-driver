# M1033 V4 Public Base Candidate B M183 Row16 Active-Set Retention Design

## Purpose

M1033 designs the next repair/projection step after M1032 localized the M1031
failure to an M183/M170 row16 normal-branch terminal-margin cliff.

M1033 is design only. It does not run repair, PPO, training, private holdout,
promotion, first replay, or actor-input changes.

## Parent Diagnosis

M1031 found temporal/exact-safe projected candidates:

```text
temporal_exact_pass_count: 16
temporal_and_exact_pass_count: 16
eligible_candidate_count: 14
```

Some projected candidates pass M267/M264 with row15 retained:

```text
M267/M264 row15 can be retained.
```

No projected candidate passes M183/M170. M1032 classifies the remaining failure
as:

```text
M183/M170 normal-branch terminal-margin active-set failure
```

Closest miss:

```text
candidate: raw_conflict_s40 alpha 0.05
M267/M264: 17/17 success drops
M183/M170: 16/17 success drops
failed row: 16
baseline normal_margin: +0.001316
candidate normal_margin: -0.000165
candidate wrong_history_successes: 0/17
```

This is not rejected-history sensitivity loss. The wrong-history branch remains
unsafe; the normal branch crosses the terminal margin boundary.

## Design Goal

The next implementation must make M183/M170 row16 normal retention a hard
active-set constraint before another repair/projection attempt.

The hard active set should include:

```text
1. P0 actor-input contract unchanged
2. M997 temporal exact retention
3. M297/M270 exact no-regression
4. M267/M264 row15 rejected-history failure retention
5. M183/M170 row16 normal branch retention
```

Only after those pass should first replay or a full public gate run.

## Retention Data Source

Use the M183/M170 boundary-outcome corpus row16:

```text
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
row_id: 16
```

Reconstruct the Candidate B normal-history rollout from the relocated outcome
snapshot, using the same logic as `boundary_outcome_replay_gate`:

```text
collect_requested_outcome_snapshots
relocate_outcome_snapshot
replay_outcome_variant(..., variant="normal")
```

Export a trajectory-action anchor with the existing `TrajectoryActionAnchor`
schema:

```text
observation
hidden
reference_action
source_index
step_index
weight
optional radius
```

The anchor should be normal-branch only:

```text
initial hidden = relocated normal history hidden
reference action = Candidate B deterministic normal action at each step
```

Do not anchor the wrong-history branch for M183/M170 row16 in this milestone;
M1032 showed the wrong-history branch remains unsafe. The failure is normal
success loss.

## Why Trajectory Anchor, Not First Action Only

M1032 row16 first-action drift is small:

```text
normal first action baseline:
  steer 0.719287, throttle -0.223611, brake -0.010006

normal first action raw alpha 0.05:
  steer 0.719968, throttle -0.222315, brake -0.011704
```

But terminal margin changes:

```text
+0.001316 -> -0.000165
```

So a first-action-only anchor is too weak. The retention term should cover a
short normal trajectory prefix or the full continuation until termination. This
matches the existing `TrajectoryActionAnchor` mechanism used by earlier repair
passes.

## Implementation Scope For M1034

M1034 should implement an export-only/no-update tool:

```text
autodrift.m183_row16_active_set_anchor_export
```

Inputs:

```text
--checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
--corpus runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
--row-id 16
--env-config configs/m121_human_view_zero_obstacle_relvel.json
--max-continuation-steps 60
```

Outputs:

```text
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.csv
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/summary.json
```

Required sanity checks:

```text
anchor loads with load_trajectory_action_anchor
row_id 16 is present exactly once as source row
anchor rows > 0
normal branch only
actor_inputs_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
```

M1034 should not run repair. It only exports and validates the active-set data.

## Later Repair Use

After M1034, a later repair/projection implementation can call
`exact_post_ppo_repair` with:

```text
--replay-trajectory-anchor-npz <combined anchor>
--lambda-replay-trajectory-anchor <high enough hard-active-set value>
```

The combined anchor should include:

```text
existing M293 rejected-history trajectory anchor
new M183/M170 row16 normal trajectory anchor
```

Gate order for that later repair:

```text
1. no actor-input change
2. exact M997 temporal retention
3. exact M297/M270 no-regression
4. exact active-set trajectory anchor sanity
5. M267/M264 first replay, row15 retained
6. M183/M170 first replay, row16 normal retained
7. only then full public gate design
```

## Non-Goals

M1033 and M1034 must not:

- run PPO;
- run a repair optimizer;
- promote a checkpoint;
- use private holdout;
- relax M997 thresholds;
- change actor inputs;
- claim full first-replay or full public-gate success.

## Decision

```text
candidate_b_m183_row16_active_set_retention_design_admit_anchor_export
```

Next milestone:

```text
m1034-v4-public-base-candidate-b-m183-row16-active-set-anchor-export
```
