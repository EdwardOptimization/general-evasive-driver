# M501 Natural Boundary Action-Sensitive Redesign

## Purpose

M501 turns the M500 negative result into the next proof path. It does not run
training, PPO, proof gates, or checkpoint promotion.

## M500 Failure Mode

M500 proved that the full M495 surface contains stronger wrong-history action
trajectory differences than the M496 targeted subset:

```text
M498 wrong-history trajectory mean: 0.055405
M500 targeted trajectory mean:      0.228203
M500 targeted trajectory p90:       0.360038
```

But the selected rows are not admissible for outcome proof:

```text
targeted_pair_count:         171
required targeted rows:   >= 240

single_config_share:       0.725146
required max share:     <= 0.70

targeted_normal_margin_min: 0.932188
eligible rows normal_margin <= 0.25: 0
targeted rows normal_margin <= 0.25: 0
```

This is the key result:

```text
action-sensitive does not imply outcome-sensitive.
```

The M500 selector found rows where wrong-history changes actions, but those
rows mostly have too much clearance slack. Running another outcome gate on that
surface would likely test high-margin action variation rather than self-ID
necessity.

## Boundary Audit

Using the M500 candidate table:

```text
normal_margin <= 0.25:
  boundary rows: 325
  first-action-pass rows: 5
  trajectory-pass rows: 0

normal_margin <= 1.0:
  boundary rows: 796
  first-action-pass rows: 13
  trajectory-pass rows: 6
  eligible seed count: 1
  eligible configs: short_reveal only

normal_margin <= 1.5:
  boundary rows: 1116
  first-action-pass rows: 25
  trajectory-pass rows: 14
  eligible seed count: 3
  eligible configs: short_reveal only

normal_margin <= 3.0:
  boundary rows: 2632
  first-action-pass rows: 111
  trajectory-pass rows: 88
  eligible seed count: 5
  eligible configs: short_reveal 61, warmup_capability 27
```

Direct selector repair is therefore not enough. At strict boundary thresholds,
the current natural configs do not contain a source-diverse surface where
one-shot wrong-history both moves the short-horizon action trajectory and sits
near the outcome boundary.

## Redesign Choice

Do not admit an M501 outcome gate.

Do not simply lower M500 thresholds, because that would select weak trajectory
rows or high-margin rows after seeing the result.

The next step should first create and sampling-validate a more boundary-pressured
natural task family, while preserving the P0 actor contract:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
no wheel/slip/mu/oracle actor inputs
```

## Proposed M502 Configs

M502 should implement two config variants.

### Short-Reveal Boundary Pressure

Start from `m494_natural_belief_short_reveal_zero_relvel`, but push the
obstacle distribution closer to the boundary:

```text
track_width: 7.2
speed_range: [14.4, 19.0]
obstacle.distance_range: [3.5, 16.0]
obstacle.half_width_range: [0.85, 1.70]
obstacle.max_threshold_score: 0.30
obstacle.perception_reveal_distance: 6.0
obstacle.min_time_after_friction_step: 0.30
randomization.mu_range: [0.14, 0.66]
actuator_tau_scale_range: [1.00, 4.20]
```

### Warm-Up Boundary Pressure

Start from `m494_natural_belief_warmup_capability_zero_relvel`, but reduce the
clearance slack while keeping pre-reveal capability evidence:

```text
track_width: 7.4
speed_range: [13.6, 18.4]
obstacle.distance_range: [5.5, 19.0]
obstacle.half_width_range: [0.75, 1.60]
obstacle.max_threshold_score: 0.28
obstacle.perception_reveal_distance: 7.5
obstacle.min_time_after_friction_step: 0.50
randomization.mu_range: [0.16, 0.70]
actuator_tau_scale_range: [0.90, 4.00]
```

These are not proof claims. They are candidate task distributions that should
be validated before mining.

## M502 Sampling Gate

M502 should only admit mining if both configs pass reset sampling:

```text
seed blocks: 12400, 12500, 12600
resets per block: 128
reset_success: 384/384 per config
label_count >= 2 per config
single_label_share <= 0.85
hidden_at_reset_count == 384
friction_step_before_reveal_count >= 300
threshold_score_mean <= M494 corresponding mean
```

Behavior smoke should compare `m399`, heuristic, and random:

```text
episodes: 32 per config/policy seed block
m399 success must be nonzero
m399 success should not be saturated above 0.90
heuristic/random should not dominate m399
```

## M503 Mining Admission

Only after M502 sampling passes should M503 mine matched-current pairs.

M503 should use a boundary-aware admission metric, not M496 target-z triage
alone and not M500 action-only triage alone:

```text
boundary_action_score =
  action_sensitive_score
+ normal_boundary_bonus
+ low_margin_bonus
+ wrong_margin_gap_proxy
- high_slack_penalty
```

Pre-registered row requirements before outcome gates:

```text
targeted_pair_count >= 240
probe_seed_count >= 6
label_count >= 2
target_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
single_config_share <= 0.70
rows with normal_margin <= 0.50 >= 40
rows with normal_margin <= 1.00 >= 100
targeted_trajectory_mean >= 0.12
targeted_trajectory_p90 >= 0.20
```

## Decision

```text
admit_m502_natural_boundary_pressure_config_implementation
```

M502 should implement and sampling-validate boundary-pressured natural belief
configs. It should not run matched-current mining, outcome gates, training, or
checkpoint promotion until the sampling/behavior gates pass.
