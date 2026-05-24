# M541 Matched-History Variance Config Family

## Purpose

M541 implements the V0 config-family step from M540. It adds a matched
4096-step L0/L2/L3 training-variance config family and tests the fairness
boundary before any training is launched.

This milestone is infrastructure-only. It does not train or promote a
checkpoint.

## Added Configs

```text
configs/ppo_m541_matched_l0_variance_4096.json
configs/ppo_m541_matched_l2_variance_4096.json
configs/ppo_m541_matched_l3_variance_4096.json
```

Shared budget:

```text
total_steps = 4096
rollout_steps = 64
num_envs = 4
update_epochs = 2
minibatch_size = 128
hidden_size = 64
learning_rate = 0.0003
eval_episodes = 5
seed = 3540
```

Approved history-level differences:

| Level | Actor Encoder | Actor History Length | Env History Length | Recurrent Sequence Training |
| --- | --- | ---: | ---: | --- |
| L0 | `mlp` | `1` | `1` | no |
| L2 | `temporal_gru` | `4` | `4` | no |
| L3 | `human_view_online_gru` | `1` | `1` | yes |

All other PPO and environment task-distribution fields are matched.

## Tests

`tests/test_history_baseline_configs.py` now checks:

- M531 short-train configs still declare valid P0 history-baseline metadata;
- M541 4096-step configs declare valid P0 history-baseline metadata;
- M541 configs share the same task distribution except for intended
  `history_length`;
- M541 differs from M531 only in `total_steps` and default `seed`.

Focused validation:

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_history_baseline_configs.py
9 passed
```

## Interpretation

The 4096-step matched config family is ready for a route pilot. The route pilot
should run the three levels on seed `3540` and check metadata, training route,
and smoke eval outputs before expanding to multiple seeds.

No performance comparison should be made until all three route-pilot runs finish
and are evaluated with the same public frozen-source pipeline.

## Decision

```text
matched_variance_config_family_pass_admit_m542_route_pilot
```
