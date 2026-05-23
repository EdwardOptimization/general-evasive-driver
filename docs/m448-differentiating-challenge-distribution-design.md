# M448 Differentiating Challenge Distribution Design

M448 designs the next scenario-distribution branch after M447 showed that the
recent checkpoint family is functionally indistinguishable on the M121
distribution. No training, PPO, benchmark run, checkpoint promotion, or actor
input/output change is part of this milestone.

## Problem

M447 compared M399 against proof-safe and proof-rejected candidates over 512
fresh seeds and 2048 candidate comparisons:

```text
success flips:             0
collision flips:           0
margin sign flips:         0
near-boundary margin rows: 0
large-margin rows:         0
return-delta rows:         3
```

That result makes the active-boundary/recovery-retention branch low leverage on
the current M121 task distribution. The distribution is good for regression
testing, but it is too insensitive to expose useful differences among recent
checkpoints.

The next step is to create fresh challenge distributions that deliberately
increase near-boundary pressure while preserving the human-view actor contract.

## Constraints

Keep the mainline actor contract:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden
```

Do not add actor inputs:

```text
mu, mass, tire, brake scale, actuator tau
slip or tire forces
feasibility labels
TTC or required clearance
path/reference features
policy labels or proof labels
```

Challenge-distribution fields may be used for logging, mining, and diversity
selection only.

## Proposed Config Family

M449 should add two config variants. Both keep:

```text
history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
wheel_observation_mode = none
road_lookahead_count = 8
obstacle_slots = 4
```

### Variant A: Near-Threshold

Purpose: sample scenarios closer to the AES/drift/unavoidable label boundary.

Suggested config:

```text
track_width = 8.0
speed_range = [12.5, 17.0]
obstacle.distance_range = [3.0, 22.0]
obstacle.half_width_range = [0.60, 1.30]
obstacle.max_threshold_score = 0.08
obstacle.stable_aes_beta_limit = 0.18
obstacle.min_time_after_friction_step = 0.05
randomization.mu_range = [0.20, 0.70]
randomization.brake_scale_range = [0.45, 1.35]
randomization.tire_stiffness_scale_range = [0.45, 1.45]
randomization.actuator_tau_scale_range = [0.75, 3.50]
```

Expected effect: more margin-sign and near-boundary margin differences without
making every scenario impossible.

### Variant B: Late High-Energy

Purpose: push the closed-loop driver into faster, shorter-time emergency
decisions.

Suggested config:

```text
track_width = 7.5
speed_range = [14.0, 18.0]
obstacle.distance_range = [2.5, 18.0]
obstacle.half_width_range = [0.75, 1.40]
obstacle.max_threshold_score = 0.12
obstacle.stable_aes_beta_limit = 0.18
obstacle.min_time_after_friction_step = 0.05
randomization.mu_range = [0.18, 0.65]
randomization.mass_scale_range = [0.85, 1.35]
randomization.cg_shift_range = [-0.16, 0.16]
randomization.tire_stiffness_scale_range = [0.42, 1.35]
randomization.brake_scale_range = [0.42, 1.30]
randomization.actuator_tau_scale_range = [0.90, 3.80]
```

Expected effect: lower base success and more sensitivity to timing, actuator
lag, low friction, and yaw authority.

## M449 Smoke Plan

M449 should implement both configs and run a small diagnostic benchmark for
each:

```text
episodes = 128
seed = 9800
policies = heuristic + M399 + M427 + M434 + M438 + M442
```

Then run the policy-difference miner on each output.

M449 acceptance should be diagnostic, not promotional:

| Check | Desired range |
| --- | --- |
| M399 success | between `0.45` and `0.90` |
| candidate success flips | at least `1`, or explain absence |
| non-return divergence rows | at least `1`, or explain absence |
| sampling failures | `0` |
| actor contract changes | `0` |

If both configs are too easy, tighten `max_threshold_score`, obstacle distance,
or speed in the next design. If both are too hard, widen distance or lower
speed. Do not tune checkpoints from the smoke result.

## Mining Decision

If M449 produces source-diverse success/collision/margin divergences, the next
step should build a challenge-distribution replay/proof gate from those rows.

If M449 still produces only return deltas or no divergences, then the current
candidate family is not a useful branch for this simulator distribution. The
research should move to a new training objective or richer task family, not
another local repair of M427/M438/M442.

## Decision

M448 passes as a design milestone and admits:

```text
m449-challenge-distribution-config-implementation
```

M449 should add the two configs, run smoke benchmarks, run the
policy-difference miner, and document whether either challenge distribution
actually separates the checkpoint family.
