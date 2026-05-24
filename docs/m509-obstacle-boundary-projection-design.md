# M509 Obstacle-Boundary Projection Design

## Purpose

M509 designs the next proof path after M508 shows that natural terminal-boundary
anchor mining finds many low-margin anchors and real one-shot wrong-history
action signal, but still cannot produce a source-capped outcome surface.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## M508 Failure Mode

M508 succeeded on the parts that M506 lacked:

```text
anchor_count:                 3246
rows normal margin <= 0.50:     97
rows normal margin <= 1.00:    104
targeted_trajectory_mean: 0.092899
targeted_trajectory_p90:  0.130059
```

But it failed source-capped outcome admission:

```text
pair_count:          104
required:            240

single_label_share:  0.826923
required:         <= 0.70
```

The key audit result is that the eligible rows collapse into only five obstacle
geometry buckets, mostly `unavoidable`:

```text
eligible obstacle_bucket_count: 5
dominant label: unavoidable
```

This means M508 did not fail because one-shot wrong-history action signal is
absent. It failed because natural low-clearance M502 states are too concentrated
near a small set of late obstacle geometries.

## Design Choice

The next step should use obstacle-boundary projection as an explicitly labelled
projection-proof branch.

The branch should start from M508 natural anchors, not from arbitrary synthetic
states:

```text
1. load M508 anchors.csv and source rows;
2. reconstruct the natural anchor snapshot from seed/step;
3. minimally relocate the obstacle in ego/body coordinates;
4. recompute the P0 observation from the relocated simulator state;
5. replay normal and one-shot wrong_matched_history from that relocated state;
6. select source-diverse rows by projected geometry, source seed, label,
   target, and config;
7. report projection magnitudes before admitting any outcome gate.
```

This keeps the ego state, actuator state, recurrent hidden state, road context,
and action-response history natural. Only the obstacle geometry is projected.

## Projection Contract

Projection is allowed only as a diagnostic proof surface. It must be clearly
separated from raw natural-scenario evidence.

Required metadata per projected row:

```text
source_obstacle_body_x
source_obstacle_body_y
projected_obstacle_body_x
projected_obstacle_body_y
projected_obstacle_half_width
projection_dx
projection_dy
projection_l2
projection_bucket
projection_family
snapshot_relocated = true
proof_surface_type = obstacle_boundary_projection
```

Hard constraints:

```text
do not change ego state;
do not change vehicle hidden dynamics;
do not change recurrent hidden state except by normal policy rollout;
do not inject hidden-hold variants;
do not add privileged actor inputs;
do not claim projection rows as raw natural proof.
```

The implementation should reuse or adapt the existing snapshot relocation
semantics from `outcome_sensitive_corpus.relocate_obstacle_snapshot`, because
that helper already preserves history and recomputes the current obstacle
observation.

## Projection Grid

M510 should use a small bounded body-frame grid around each M508 anchor:

```text
longitudinal targets:
  max(3.0, source_x - 2.0)
  max(3.0, source_x - 1.0)
  max(3.0, source_x + 0.0)
  max(3.0, source_x + 1.0)
  max(3.0, source_x + 2.0)
  4.0
  6.0
  8.0

lateral offsets:
  source_y - 1.0
  source_y - 0.5
  source_y + 0.0
  source_y + 0.5
  source_y + 1.0
```

Rows should be rejected if the projected geometry is outside road/free-space
limits or if projection magnitude exceeds the configured diagnostic cap.

Suggested initial caps:

```text
projection_l2 <= 6.0 m for primary rows
projection_l2 <= 10.0 m for diagnostic rows
```

Admission should prefer primary rows. Diagnostic rows can explain failure modes
but should not satisfy the main gate unless the manifest explicitly says so
before running.

## M510 Admission Gate

M510 should admit an outcome gate only if the selected projected surface passes:

```text
pair_count >= 240
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
single_config_share <= 0.70

rows normal_margin <= 0.50 >= 40
rows normal_margin <= 1.00 >= 100
targeted_trajectory_mean >= 0.04
targeted_trajectory_p90 >= 0.08

projection_l2_p50 <= 3.0
projection_l2_p90 <= 6.0
primary_projection_share >= 0.80
```

The outcome gate remains forbidden if the surface only passes after using large
diagnostic projection moves.

## Decision

```text
admit_m510_obstacle_boundary_projection_miner
```

Next blocker:

```text
m510-obstacle-boundary-projection-miner
```
