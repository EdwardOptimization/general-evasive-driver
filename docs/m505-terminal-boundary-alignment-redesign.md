# M505 Terminal Boundary Alignment Redesign

## Purpose

M505 redesigns the next proof path after M504 showed that boundary-pressure
configs and the M500 action selector still do not produce enough rows that are
both action-sensitive and low-margin.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## M504 Blocker

M504 selected rows with a strong wrong-history action trajectory signal:

```text
targeted_trajectory_mean: 0.224056
targeted_trajectory_p90:  0.348210
```

But the selected surface failed terminal-boundary coverage:

```text
targeted_pair_count: 195   required >= 240
normal_margin <= 0.50: 4   required >= 40
normal_margin <= 1.00: 6   required >= 100
```

Therefore, running an outcome gate on M504 targeted rows would mostly test
high-margin action variation again.

## Boundary-First Audit

The full M504 candidate table contains many low-margin normal-history rows,
but their wrong-history action perturbations are smaller than the M500
threshold:

```text
normal_margin <= 0.50:
  rows: 250
  seeds: 6
  labels: 2
  targets: 3
  configs: 2
  first_action mean / p90: 0.0296 / 0.0666
  trajectory mean / p90:   0.0274 / 0.0625

normal_margin <= 1.00:
  rows: 591
  seeds: 6
  labels: 2
  targets: 3
  configs: 2
  first_action mean / p90: 0.0328 / 0.0752
  trajectory mean / p90:   0.0322 / 0.0746
```

With softer action thresholds, the boundary-action pool is source-diverse:

```text
thresholds:
  first_action >= 0.04
  or trajectory_mean >= 0.04
  or trajectory_max >= 0.08

normal_margin <= 0.50:  65 rows
normal_margin <= 1.00: 216 rows
normal_margin <= 2.00: 494 rows
normal_margin <= 3.00: 945 rows
```

This suggests the previous selector order was wrong. At low terminal margin,
small action differences may matter, so requiring M500-scale action movement
first discards the rows most relevant to outcome proof.

## Redesign

The next selector should invert the order:

```text
old:
  action-sensitive first
  then inspect terminal margin

new:
  terminal-boundary-sensitive first
  then require a smaller but nonzero wrong-history action perturbation
```

This keeps the intervention natural:

```text
wrong-history remains one-shot;
hidden is not clamped;
actions are closed-loop after the branch point;
actor input contract is unchanged.
```

It is less artificial than hidden-hold forcing because it does not change the
policy dynamics after the decision point. It only changes which naturally
sampled rows are selected for proof.

## M506 Selector

M506 should implement a terminal-boundary-aware selector over the M504
candidate table.

Inputs:

```text
runs/m504_boundary_action_sensitive_targeted_pair_triage/action_sensitive_candidates.csv
```

Stage 1: Boundary anchor filter:

```text
normal_min_clearance_margin <= 2.0
```

Stage 2: Soft action-sensitivity filter:

```text
first_action_distance >= 0.04
or action_trajectory_distance_mean >= 0.04
or action_trajectory_distance_max >= 0.08
```

Stage 3: Score:

```text
score =
  2.0 * low_margin_bonus(normal_margin)
+ 1.0 * clipped(action_trajectory_distance_mean / 0.12)
+ 0.75 * clipped(first_action_distance / 0.12)
+ 0.50 * clipped(action_trajectory_distance_max / 0.25)
+ 0.25 * clipped(target_z_delta / 4.0)
+ label_priority
```

Stage 4: Source-diverse export caps:

```text
max_rows: 300
max_per_probe_seed: 60
max_per_left_seed: 6
max_per_label: 150
max_per_target: 130
max_per_config: 160
max_per_offset: 90
max_per_obstacle_bucket: 20
```

## M506 Admission Gate

M506 should only admit an outcome gate if:

```text
targeted_pair_count >= 240
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
single_config_share <= 0.70

rows normal_margin <= 0.50 >= 40
rows normal_margin <= 1.00 >= 100
rows normal_margin <= 2.00 >= 180

targeted_trajectory_mean >= 0.04
targeted_trajectory_p90 >= 0.08
```

If M506 fails, the next step should be terminal-boundary anchor mining or
obstacle-boundary projection, not another action-first selector.

## Decision

```text
admit_m506_terminal_boundary_aware_selector
```

M506 should implement and run the terminal-boundary-aware selector. It should
not run outcome gates, train, or promote a checkpoint.
