# M499 Natural Belief Action-Sensitive Selector Design

## Purpose

M499 designs the next selector after M498 showed that the M496 target-z triage
does not select outcome-relevant wrong-history trajectories.

No experiment run, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Blocker From M498

M498 classified the M497 failure as:

```text
weak_wrong_history_trajectory_signal
```

Key numbers:

```text
wrong_tail_once trajectory mean: 0.055405
reset_tail trajectory mean:      1.005724
zero_current trajectory mean:    0.451155

wrong / reset trajectory ratio:        0.055089
wrong / zero-current trajectory ratio: 0.122806
```

The first action can move, but the wrong-history branch rapidly corrects:

```text
wrong_tail_once first-action mean: 0.069847
zero_current first-action mean:    0.083332
```

Therefore, repeating M496 target-z triage and immediately running another
outcome gate is not justified.

## Design Goal

Select natural matched-current rows where wrong-history actually changes the
short-horizon closed-loop action trajectory before current-response correction
dominates.

This selector is still diagnostic. It does not add actor inputs, change the
policy, use hidden-hold, train, or promote a checkpoint.

## Proposed M500 Tool

Implement:

```text
autodrift.natural_wrong_history_action_sensitive_selector
```

Inputs:

```text
--candidate-pairs-csv runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv
--checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
--env-config-map short_reveal=configs/m494_natural_belief_short_reveal_zero_relvel.json
--env-config-map warmup_capability=configs/m494_natural_belief_warmup_capability_zero_relvel.json
--decision-offsets 0,2,4,8
--short-horizon-steps 8
```

Required outputs:

```text
action_sensitive_candidates.csv
targeted_pairs.csv
summary.json
```

## Probe Semantics

For each candidate pair and decision offset:

```text
left snapshot  = left_seed, left_step + offset
right snapshot = right_seed, right_step + offset
```

Run two branches:

```text
normal branch:
  start from left snapshot and left hidden

wrong-history branch:
  start from left snapshot and right hidden
  then close the loop normally with current left observations
```

Measure:

```text
first_action_distance
short_horizon_action_trajectory_distance_mean
short_horizon_action_trajectory_distance_max
normal_min_clearance_margin
wrong_min_clearance_margin
short_horizon_margin_gap
```

Do not include persistent hidden-hold variants. Wrong-history remains a
one-shot belief swap at the decision point.

## Two-Stage Selector

### Stage 1: Broad One-Step Action Screen

Run across the full M495 surface and all offsets:

```text
5580 pairs x 4 offsets
normal action vs wrong-history action
```

Keep candidates with:

```text
first_action_distance >= 0.12
```

If this yields too many rows, keep the top rows per source group by:

```text
first_action_distance
target_z_delta
visible_similarity_score
near_boundary_proxy
```

### Stage 2: Short-Horizon Trajectory Screen

For Stage 1 rows, run an 8-step closed-loop probe:

```text
normal branch
wrong-history branch
```

Accept rows with either:

```text
trajectory_distance_mean >= 0.12
```

or:

```text
trajectory_distance_max >= 0.25
```

These thresholds are deliberately above the M498 all-row wrong-history p90
trajectory mean (`0.107307`) but below the M498 max (`0.305390`), so M500
tests whether the full M495 pool contains stronger action-sensitive rows
rather than assuming it does.

### Stage 3: Source-Diverse Targeted Export

Select up to:

```text
max_rows: 360
```

with caps:

```text
max_per_probe_seed: 70
max_per_left_seed: 8
max_per_label: 160
max_per_target: 140
max_per_config: 180
max_per_offset: 100
max_per_obstacle_bucket: 24
```

Required gate:

```text
targeted_pair_count >= 240
probe_seed_count >= 6
obstacle_label_count >= 2
target_count >= 2
config_count >= 2
offset_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
single_config_share <= 0.70
```

If the selector cannot meet these criteria, do not run another outcome gate.
Classify the branch as action-sensitive surface not found and revise task or
intervention design.

## Score

Use a score that directly includes the missing quantity from M498:

```text
score =
  2.0 * clipped(trajectory_distance_mean / 0.25)
+ 1.0 * clipped(first_action_distance / 0.25)
+ 0.5 * clipped(trajectory_distance_max / 0.50)
+ 0.5 * clipped(target_z_delta / 4.0)
+ 0.3 * near_boundary_proxy
+ label_priority
+ visible_similarity_bonus
```

`label_priority` should keep drift-required and unavoidable rows represented,
but it must not dominate action sensitivity.

## Outcome-Gate Admission

M500 should only admit M501 outcome testing if:

```text
targeted surface passes source-diversity gates
selected trajectory_distance_mean is materially above M498 baseline
normal branch remains near-boundary often enough to allow events
```

Suggested admission thresholds:

```text
selected trajectory_distance_mean >= 0.12
selected trajectory_distance_p90 >= 0.20
selected normal_margin_min <= 0.25
```

These are not proof claims. They are admission criteria for running a more
expensive outcome gate.

## Why This Is The Right Next Step

M498 shows target-z capability divergence is not enough. The actor often
corrects wrong-history after one or two steps. Therefore the next gate should
look for rows where wrong-history affects the short-horizon action trajectory
itself, rather than hoping target divergence predicts outcome sensitivity.

This keeps the research path aligned with the core claim:

```text
history should matter because it changes closed-loop actions and outcomes,
not because an offline target says two hidden conditions are different.
```

## Decision

```text
admit_m500_natural_action_sensitive_selector_implementation
```

M500 should implement and run the action-sensitive selector. It should not train
or promote a checkpoint.
