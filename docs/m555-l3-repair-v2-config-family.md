# M555 L3 Repair V2 Config Family

## Purpose

M555 implements the M554-approved L3-only repair-v2 config family.

This is infrastructure only. It does not train or promote a checkpoint.

## Added Configs

```text
configs/ppo_m555_l3_repair_epoch1_clip01_4096.json
configs/ppo_m555_l3_repair_longseq_epoch1_4096.json
configs/ppo_m555_l3_repair_lowentropy_epoch1_4096.json
```

All three preserve:

```text
actor input contract = P0_human_view_no_wheel_no_oracle
actor_encoder = human_view_online_gru
history_baseline_level = L3_online_gru
env history_length = 1
action_history_mode = full
obstacle_relative_velocity_mode = zero
total_steps = 4096
num_envs = 4
hidden_size = 64
checkpoint_interval_steps = 256
seed = 3540
device = cpu
```

The env section is identical to:

```text
configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json
```

## Variants

| Variant | Intent | PPO Changes |
| --- | --- | --- |
| `epoch1_clip01` | Reduce recurrent policy drift per update | `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `max_grad_norm = 0.25` |
| `longseq_epoch1` | Give the online GRU a longer contiguous sequence during recurrent PPO updates | `rollout_steps = 128`, `minibatch_size = 128`, `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `max_grad_norm = 0.25` |
| `lowentropy_epoch1` | Test whether stochastic policy-scale drift hurts deterministic route eval | `learning_rate = 0.0001`, `update_epochs = 1`, `clip_coef = 0.10`, `ent_coef = 0.0005`, `max_grad_norm = 0.25`, `freeze_log_std = true`, `log_std_init = -1.25` |

## Validation

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_history_baseline_configs.py
```

Result:

```text
24 passed
```

The new tests verify:

- every M555 config declares a valid L3 P0 history-baseline contract;
- all M555 env sections equal the M548 L3 update-aligned env;
- only M554-approved PPO stability fields differ from M548 fast-select;
- no extra M555 variants were added beyond the three pre-registered names.

## Next Step

M556 should train the three M555 configs and run reusable route-screen v2 over
all interval/final checkpoints as candidates, with L0/L2 references and no
public frozen-source rows.

## Decision

```text
l3_repair_v2_config_family_pass_admit_m556_route_screen_selection
```
