# M559 Targeted Collision-Margin Config Family

## Purpose

M559 implements the M558-approved collision/clearance-margin repair config
family.

This is infrastructure only. It does not train, evaluate public frozen-source
rows, or promote a checkpoint.

## Added Configs

```text
configs/ppo_m559_l3_collision35_terminal4_4096.json
configs/ppo_m559_l3_collision35_dense002_4096.json
configs/ppo_m559_l3_collision45_terminal4_4096.json
```

All three preserve the M555 `epoch1_clip01` PPO controls:

```text
learning_rate = 0.0001
update_epochs = 1
clip_coef = 0.10
max_grad_norm = 0.25
rollout_steps = 64
minibatch_size = 128
checkpoint_interval_steps = 256
```

They also preserve:

```text
actor input contract = P0_human_view_no_wheel_no_oracle
actor_encoder = human_view_online_gru
history_baseline_level = L3_online_gru
env history_length = 1
obstacle_relative_velocity_mode = zero
```

## Variants

| Variant | Reward Changes |
| --- | --- |
| `collision35_terminal4` | `collision_penalty = 35.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50` |
| `collision35_dense002` | `collision_penalty = 35.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50`, `dense_clearance_margin_reward_scale = 0.02`, `dense_clearance_margin_reward_clip = 0.50`, `dense_clearance_margin_reward_window = 8.0` |
| `collision45_terminal4` | `collision_penalty = 45.0`, `clearance_margin_reward_scale = 4.0`, `clearance_margin_reward_clip = 0.50` |

## Validation

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_history_baseline_configs.py
```

Result:

```text
28 passed
```

The new tests verify:

- P0 L3 actor contract is preserved;
- PPO controls equal M555 `epoch1_clip01`;
- env/task distribution equals M555 except the M558-approved obstacle reward
  fields;
- no extra M559 variants were added beyond the three pre-registered configs.

## Next Step

M560 should train all three configs and run route-screen v2 with fresh selection
seed `16560`, not the M556 diagnostic seed `15560`.

## Decision

```text
collision_margin_config_family_pass_admit_m560_route_screen_selection
```
