# M546 L3 Recurrent Repair Config Family

## Purpose

M546 implements the controlled L3-only repair config family designed in M545.
It does not train or promote a checkpoint.

The goal is to make the next route pilot test the actual suspected M544 failure
mode: L3 reaches a useful early policy and then degrades, while the final
checkpoint is used by default.

## Added Configs

```text
configs/ppo_m546_l3_repair_fast_select_4096.json
configs/ppo_m546_l3_repair_lr1e4_4096.json
configs/ppo_m546_l3_repair_lr5e5_4096.json
```

All three configs keep the M541 L3 environment and P0 history-baseline contract:

```text
history_baseline_level = L3_online_gru
actor_encoder = human_view_online_gru
actor_history_length = 1
env.history_length = 1
recurrent_sequence_training = true
obstacle_relative_velocity_mode = zero
wheel_observation_mode = none
```

## Config Variants

| Variant | Purpose | Allowed Changes From M541 L3 |
| --- | --- | --- |
| `fast_select` | Preserve interval checkpoints while keeping the original update size | `checkpoint_interval_steps = 512` |
| `lr1e4` | Reduce recurrent update aggressiveness | `learning_rate = 0.0001`, `max_grad_norm = 0.25`, `checkpoint_interval_steps = 512` |
| `lr5e5` | Test a more conservative recurrent update | `learning_rate = 0.00005`, `max_grad_norm = 0.25`, `checkpoint_interval_steps = 512` |

No config changes the reward, sampler, obstacle distribution, randomization
ranges, actor input contract, or route budget.

## Tests

`tests/test_history_baseline_configs.py` now checks:

- each M546 config declares valid `L3_online_gru` P0 history-baseline metadata;
- each config preserves the M541 L3 environment exactly;
- only approved optimization/checkpoint-selection controls differ from M541 L3;
- all repair configs use `checkpoint_interval_steps = 512`.

Focused validation:

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_history_baseline_configs.py
```

## Next Route Pilot

M547 should run the three repair configs on seed `3540`, collect route metrics
and interval checkpoints, then select candidates using the M545 route-only
selection rule before any public frozen-source eval.

The first route pilot should answer:

```text
Does interval selection alone recover the early L3 peak?
Does a lower recurrent learning rate prevent late collapse?
Do any repaired L3 variants pass route health before public diagnostics?
```

## Decision

```text
l3_repair_config_family_pass_admit_m547_route_pilot
```
