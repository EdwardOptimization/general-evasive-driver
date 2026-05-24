# M558 Targeted Collision-Margin Repair Design

## Purpose

M558 designs the next L3 repair branch after M557 classified M556 as:

```text
collision_dominated_margin_failure_after_binary_success_gain
```

This milestone is design-only. It does not train, evaluate public frozen-source
rows, or promote a checkpoint.

## Starting Point

M557 showed the M555 PPO-stability variants were not enough:

- `35/43` M556 L3 candidates beat L0 on binary success;
- `0/43` beat L0 on clearance margin;
- `0/43` pass L0 collision tolerance;
- the best candidate converts `5` L0 collisions to completions, but also
  converts `7` L0 non-collision terminations and `3` L0 completions to
  collisions.

The next repair should therefore target obstacle contact and clearance margin
directly. Repeating PPO stability variants alone is not justified.

## Overfit Boundary

M556 route-screen seed block:

```text
seed = 15560
episodes = 64
```

is now diagnostic evidence. It should not be reused as the next selection gate.

M560 should rotate route-screen v2 selection to:

```text
seed = 16560
episodes = 64
```

M556 seed `15560` can be reported as a known diagnostic regression check after
selection, but it must not decide which checkpoint reaches public diagnostics.

## Frozen Boundaries

Keep:

```text
actor input contract = P0_human_view_no_wheel_no_oracle
actor_encoder = human_view_online_gru
history_baseline_level = L3_online_gru
env history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
track/task/randomization ranges = M548/M555 L3
checkpoint_interval_steps = 256
```

Do not change:

- actor inputs;
- road/obstacle observation profile;
- hidden/oracle labels;
- L0/L2 references;
- route-screen v2 thresholds.

## Allowed Repair Controls

M559 may change obstacle reward terms that already exist in the simulator:

```text
obstacle.collision_penalty
obstacle.clearance_margin_reward_scale
obstacle.clearance_margin_reward_clip
obstacle.dense_clearance_margin_reward_scale
obstacle.dense_clearance_margin_reward_clip
obstacle.dense_clearance_margin_reward_window
```

Keep the M555 `epoch1_clip01` PPO stability controls:

```text
learning_rate = 0.0001
update_epochs = 1
clip_coef = 0.10
max_grad_norm = 0.25
rollout_steps = 64
minibatch_size = 128
```

Reason: among M556 candidates, the best checkpoints across families were very
similar, and `epoch1_s256` was the best by margin. The next controlled variable
should be collision/margin reward, not another PPO stability sweep.

## Candidate Config Family

M559 should add exactly three L3-only configs:

| Candidate | Intent | Changes From M555 `epoch1_clip01` |
| --- | --- | --- |
| `collision35_terminal4` | Penalize contact more and add terminal clearance pressure | `collision_penalty = 35.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50` |
| `collision35_dense002` | Add weak dense clearance pressure near the obstacle | `collision_penalty = 35.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50`, `dense_clearance_margin_reward_scale = 0.02`, `dense_clearance_margin_reward_clip = 0.50`, `dense_clearance_margin_reward_window = 8.0` |
| `collision45_terminal4` | Test stronger contact penalty without dense shaping | `collision_penalty = 45.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50` |

Do not add more variants in M559.

## Selection Rule

M560 should:

1. Train all M559 configs on seed `3540`.
2. Evaluate every interval/final checkpoint with route-screen v2 seed `16560`.
3. Include L0/L2 references using level-matched configs.
4. Require `uses_public_frozen_source_rows = false`.

Admission:

```text
pass_l0_success
pass_l0_margin
pass_l0_collision_tolerance
```

If no checkpoint clears L0 on the fresh route-screen seed, stop and classify as:

```text
training_instability
promotion_gate_failure
```

If a checkpoint clears L0 but is far below L2, it may enter public diagnostics
only as a repair diagnostic, not as evidence that L3 beats finite-window L2.

## Public Boundary

Only after M560 route-screen v2 admits a checkpoint:

- run public frozen-source diagnostics;
- compare against L0, L2, M542 L3, M549, and M556 best candidates;
- keep public results diagnostic unless a later frozen recipe passes matched
  multi-seed and fresh-holdout gates.

## Decision

```text
targeted_collision_margin_repair_design_admit_m559_config_family
```
