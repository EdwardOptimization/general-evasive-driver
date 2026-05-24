# M697 Fresh Trajectory-Boundary Sampling Design

## Purpose

M697 designs a fresh scenario sampler for the
`trajectory_terminal_boundary_source_mining` branch.

The key change from M695:

```text
Do not start from M692 replay rows.
Sample fresh scenarios and candidate snapshots directly from environment
rollouts, then test terminal-margin sensitivity.
```

This milestone is design-only:

```text
no mining run
no actor training
no PPO
no checkpoint promotion
no actor-input change
```

## Background

M695 found:

```text
rows_attempted:                  40
normal_success_candidates:       15
normal_failed_rejected:          25
trajectory_sensitive_rows:        0
history_action_critical_rows:     0
accepted_rows:                    0
result_class:         surface_empty
```

M696 classified this as a scenario sampling failure on inherited M692 rows, not
as proof that terminal-boundary mining is impossible.

M697 therefore designs a sampler whose primary object is:

```text
fresh snapshot candidates around obstacle/boundary interaction windows
```

not:

```text
old output-residual proof rows
```

## Design Principle

The miner should be two-stage:

```text
Stage 1:
  cheaply collect many candidate snapshots from fresh base-actor rollouts

Stage 2:
  run expensive perturbation and wrong-history sensitivity only on snapshots
  likely to be near terminal-margin boundaries
```

This avoids the M695 failure mode where the source surface was predetermined by
old exact-output diagnostics.

## Scenario Sampling

Initial surfaces:

```text
fresh=configs/ppo_m541_matched_l3_variance_4096.json
ood=configs/eval_m574_moderate_ood_l3.json
```

Seed plan:

```text
seed_start: 30000
seed_count: 512
surface allocation:
  fresh: 256 seeds
  ood:   256 seeds
```

The seed range should be configurable. The implementation must record:

```text
surface
seed
config path
sampled obstacle label if available for logging only
sampled hidden parameters if available for logging only
episode termination reason
episode terminal margin
```

Hidden parameters and obstacle labels remain forbidden actor inputs. They are
allowed only for offline stratification and debugging.

## Snapshot Collection Window

During each base-actor rollout, collect snapshots at fixed cadence after the
obstacle is plausibly relevant.

Candidate signals:

```text
obstacle longitudinal distance in ego/path frame
obstacle perception visible
min clearance margin is finite
episode not terminal
step within configured window
```

Initial filters:

```text
min_step: 10
max_step: env_config.max_steps - 2
snapshot_stride: 3
obstacle_longitudinal_min: -5.0
obstacle_longitudinal_max: 80.0
max_snapshots_per_episode: 8
```

If direct obstacle longitudinal distance is unavailable, the implementation may
use obstacle slot x-position from the P0 observation as a deployable proxy for
candidate-window selection.

The sampler should write skipped-window reasons:

```text
obstacle_not_visible
outside_step_window
outside_distance_window
episode_terminated
snapshot_budget_exceeded
```

## Normal-History Prepass

For each candidate snapshot, run a short normal-history continuation:

```text
first action: base actor action
continuation: unchanged base actor
max_continuation_steps: 40
```

Reject from action-critical acceptance if:

```text
normal_success == false
normal_collision == true
normal_off_road == true
normal_spin_out == true
normal_margin is non-finite
normal_margin < 0.0
```

Keep rejected rows in `rejected_rows.csv`.

Boundary buckets:

```text
terminal_cliff:       0.00 <= normal_margin <= 0.02
near_boundary:        0.02 <  normal_margin <= 0.15
wide_but_sensitive:   0.15 <  normal_margin <= 0.50
too_safe:             normal_margin > 0.50
```

The first implementation should test `terminal_cliff`, `near_boundary`, and
`wide_but_sensitive`. It should usually reject `too_safe` unless perturbation
sensitivity is strong enough to create a success/collision/off-road/spin flip.

## Perturbation Sensitivity

Use the same first-action override contract as M695:

```text
snapshot -> override first action -> unchanged base actor continuation
```

Initial perturbation grid:

```text
steer:    +/- 0.01, +/- 0.02, +/- 0.04
brake:    +/- 0.03, +/- 0.06
throttle: +/- 0.03, +/- 0.06
combined steer/brake pairs for nonzero steer and brake
```

Acceptance metrics:

```text
margin_sensitivity = max(candidate_margin) - min(candidate_margin)
risk_sensitivity   = max(candidate_risk)   - min(candidate_risk)
success_flip_count
collision_flip_count
off_road_flip_count
spin_flip_count
```

Initial thresholds:

```text
margin_sensitivity >= 0.02
or risk_sensitivity >= 0.02
or any success/collision/off-road/spin flip
```

The miner should also record the best improving and worst degrading candidate
actions:

```text
best_action
worst_action
best_margin
worst_margin
best_risk
worst_risk
best_minus_base_action_l2
worst_minus_base_action_l2
```

## Counterfactual-History Sensitivity

Fresh sampling does not naturally provide paired wrong-history snapshots. M697
therefore separates two labels:

```text
trajectory_boundary:
  local action perturbations affect closed-loop terminal outcome

history_action_critical:
  wrong/counterfactual history affects closed-loop terminal outcome
```

M698 should implement `trajectory_boundary` first. For
`history_action_critical`, it should provide one optional mechanism:

```text
matched_seed_pool:
  find snapshots with similar surface, obstacle window, ego velocity, yaw rate,
  lateral velocity, and step bucket, but different seed/hidden response history
```

Suggested matching tolerances:

```text
abs(vx_a - vx_b) <= 1.0 m/s
abs(vy_a - vy_b) <= 0.8 m/s
abs(yaw_rate_a - yaw_rate_b) <= 0.25 rad/s
abs(obstacle_x_a - obstacle_x_b) <= 8.0 m
abs(obstacle_y_a - obstacle_y_b) <= 1.0 m
abs(step_a - step_b) <= 8
```

Wrong-history sensitivity should only be claimed if:

```text
normal continuation is successful or near-boundary
matched-history continuation worsens margin by >= 0.01
or matched-history continuation worsens risk by >= 0.01
or matched-history creates collision/off-road/spin/success flip
```

If no matched history exists, the row can still be accepted as
`trajectory_boundary`, but it cannot support a self-ID mechanism claim.

## Source Diversity

Accepted rows must be balanced by:

```text
surface
seed
step bucket
obstacle-distance bucket
normal-margin bucket
sensitivity bucket
target label for logging only if available
hidden-condition bucket for logging only if available
```

Initial thresholds:

```text
accepted_rows >= 80
trajectory_boundary_rows >= 50
unique_seeds >= 30
unique_step_buckets >= 4
unique_distance_buckets >= 4
max_seed_dominance <= 0.08
max_bucket_dominance <= 0.25
heldout_fraction >= 0.20
```

If `history_action_critical_rows >= 20`, the source can support a later self-ID
objective design. If not, it can only support base trajectory-boundary driver
capability work.

## Artifacts For M698

M698 should write:

```text
runs/m698_fresh_trajectory_boundary_sampler/summary.json
runs/m698_fresh_trajectory_boundary_sampler/episode_summary.csv
runs/m698_fresh_trajectory_boundary_sampler/snapshot_candidates.csv
runs/m698_fresh_trajectory_boundary_sampler/prepass_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/perturbation_rollouts.csv
runs/m698_fresh_trajectory_boundary_sampler/accepted_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/rejected_rows.csv
runs/m698_fresh_trajectory_boundary_sampler/source_summary.csv
runs/m698_fresh_trajectory_boundary_sampler/split_summary.csv
```

Required summary fields:

```text
episodes_attempted
episodes_completed
snapshots_collected
prepass_rows
normal_failed_rejected
too_safe_rejected
trajectory_boundary_rows
history_action_critical_rows
accepted_rows
heldout_rows
unique_seeds
unique_step_buckets
unique_distance_buckets
margin_sensitivity_mean
margin_sensitivity_p95
risk_sensitivity_mean
risk_sensitivity_p95
success_flip_count
collision_flip_count
result_class
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

## Result Classes

M698 should classify:

```text
fresh_source_positive:
  accepted rows and diversity thresholds pass

fresh_source_sparse:
  sensitive rows exist but volume or diversity is insufficient

normal_failed_only:
  candidate windows exist but normal-history continuations already fail

too_safe_only:
  candidate windows exist but all are far from terminal boundary and insensitive

history_insensitive:
  trajectory_boundary rows exist but matched/counterfactual history has no
  outcome effect

fresh_surface_empty:
  no meaningful sensitive rows are found

implementation_failed:
  artifacts or replay construction are incomplete
```

Only `fresh_source_positive` can admit objective design.

## Negative-Result Rules

If `fresh_surface_empty`:

```text
audit before changing thresholds
inspect whether snapshot windows miss the obstacle interaction
inspect whether perturbation grid is too small
```

If `normal_failed_only`:

```text
do not claim self-ID source mining failure
consider base driver capability improvement
```

If `too_safe_only`:

```text
move sampling closer to obstacle and boundary windows
```

If `history_insensitive`:

```text
separate base evasive capability from self-ID mechanism evidence
```

## Decision

M697 admits M698 implementation.

Blocked until M698:

```text
objective design
actor update
PPO
checkpoint promotion
self-ID mechanism claims from this branch
```

## Decision String

```text
fresh_trajectory_boundary_sampling_design_admit_m698
```

## Next

```text
m698-fresh-trajectory-boundary-sampler-implementation
```
