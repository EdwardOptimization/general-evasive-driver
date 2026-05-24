# M511 Label-Targeted Projection Design

## Purpose

M511 designs the next projection-proof path after M510 shows that small
obstacle-boundary projections preserve action signal but keep every projected
row in the `unavoidable` label.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## M510 Failure Mode

M510 passes the projection-magnitude and action-signal parts:

```text
projection_l2_p50:        1.000000
projection_l2_p90:        1.118034
primary_projection_share: 1.000000
targeted_trajectory_mean: 0.089577
targeted_trajectory_p90:  0.125161
```

It fails the admission gate because the projected surface is label-degenerate:

```text
pair_count:              102
obstacle_label_count:      1
single_label_share:    1.000
projected label: unavoidable only
```

This means bounded local projection is too conservative to cross the simulator
scenario-label boundary. The next projection branch must target scenario labels
explicitly, while continuing to report projection magnitude and keeping the
actor input clean.

## Design Choice

M512 should implement a label-targeted projection miner.

The miner should:

```text
1. start from M508/M510 natural source pairs;
2. reconstruct natural left/right snapshots;
3. enumerate obstacle body_x, body_y, and half_width candidates;
4. use simulator scenario classification only for offline mining;
5. keep projected rows only when the relocated snapshot label matches a
   requested target label family;
6. replay normal and one-shot wrong_matched_history;
7. select source-diverse rows across projected label, target, config, seed, and
   projection bucket.
```

The actor still sees only the normal P0 observation from the relocated state.
The projected label is logging/gate metadata, not an actor input.

## Projection Families

Use explicit target families:

```text
target_projected_labels:
  drift_required
  unavoidable
  aes_feasible
```

The primary gate should require at least two labels. `aes_feasible` is allowed
as additional diversity, but the first pass should not require all three labels
because the M502 boundary-pressure source states may not support clean
`aes_feasible` projection without large geometry moves.

Candidate grid:

```text
body_x_absolute:
  4, 6, 8, 10, 12, 14

body_y_from_source:
  source_y - 1.5
  source_y - 1.0
  source_y - 0.5
  source_y + 0.0
  source_y + 0.5
  source_y + 1.0
  source_y + 1.5

half_width_scale:
  0.75, 1.0, 1.25
```

Rows should be rejected if projection magnitude or half-width change is outside
the pre-registered limits.

## Admission Gate

M512 should admit an outcome gate only if:

```text
pair_count >= 240
probe_seed_count >= 6
projected_obstacle_label_count >= 2
target_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_projected_label_share <= 0.70
single_config_share <= 0.70

rows normal_margin <= 0.50 >= 40
rows normal_margin <= 1.00 >= 100
targeted_trajectory_mean >= 0.04
targeted_trajectory_p90 >= 0.08

projection_l2_p50 <= 5.0
projection_l2_p90 <= 8.0
half_width_delta_abs_p90 <= 0.40
primary_projection_share >= 0.80
```

The magnitude caps are intentionally looser than M510 because label-targeted
projection must sometimes move farther than a local boundary nudge. The surface
must still be labelled projection proof, not natural-scenario proof.

## Forbidden Shortcuts

Do not:

```text
relax projected-label diversity after seeing the result;
use projected labels as actor inputs;
change ego state or hidden dynamics;
use hidden-hold variants;
count large diagnostic projection rows toward primary admission;
claim projected rows as raw natural proof.
```

## Decision

```text
admit_m512_label_targeted_projection_miner
```

Next blocker:

```text
m512-label-targeted-projection-miner
```
