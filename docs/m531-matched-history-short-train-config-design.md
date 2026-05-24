# M531 Matched History Short-Train Config Design

## Purpose

M531 defines a machine-checkable short-train config family for matched
history-baseline comparisons. This prevents the next comparison from becoming
three separately tuned runs.

No training is run in M531. No checkpoint is promoted.

## Config Family

Added:

```text
configs/ppo_m531_matched_l0_short_train.json
configs/ppo_m531_matched_l2_short_train.json
configs/ppo_m531_matched_l3_short_train.json
```

Shared PPO budget:

```text
total_steps = 1024
rollout_steps = 64
num_envs = 4
update_epochs = 2
minibatch_size = 128
hidden_size = 64
learning_rate = 0.0003
eval_episodes = 5
seed = 3530
device = cpu
```

Shared task distribution:

```text
M502-style boundary-pressure short-reveal task
P0 no-wheel/no-privileged/no-oracle observation contract
obstacle_relative_velocity_mode = zero
same road, obstacle, friction-step, and hidden-dynamics randomization
```

The only intended env difference is history length:

```text
L0: history_length = 1
L2: history_length = 4
L3: history_length = 1
```

## Baseline Levels

```text
L0_current_observation:
  actor_encoder = mlp
  actor_history_length = 1
  history_baseline_level = L0_current_observation

L2_finite_window:
  actor_encoder = temporal_gru
  actor_history_length = 4
  history_baseline_level = L2_finite_window

L3_online_gru:
  actor_encoder = human_view_online_gru
  actor_history_length = 1
  recurrent_sequence_training = true
  history_baseline_level = L3_online_gru
```

L1 remains an annotation rather than a separate config because the current P0
frame already contains previous physical commands and current actuator/IMU-like
response. Splitting L1 cleanly would require a stricter frame profile and should
not be mixed into this first matched short-train family.

## Validation

Added `tests/test_history_baseline_configs.py`, which checks:

```text
all three configs declare valid history_baseline_level values;
all three pass P0 history-baseline validation;
all three share the same PPO budget;
all three share the same task distribution except history_length;
L2 uses a finite window with actor_history_length = env history_length = 4.
```

Smoke validation command:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_history_baseline_configs.py tests/test_history_baselines.py
```

Result:

```text
11 passed
```

## Next Executable Milestone

M532 should run the three configs once on the shared seed `3530`:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m531_matched_l0_short_train.json \
  --device cpu \
  --run-dir runs/m532_matched_l0_short_train_seed3530

PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m531_matched_l2_short_train.json \
  --device cpu \
  --run-dir runs/m532_matched_l2_short_train_seed3530

PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m531_matched_l3_short_train.json \
  --device cpu \
  --run-dir runs/m532_matched_l3_short_train_seed3530
```

M532 should still be treated as a short-train route check. It can report return
and termination metrics, but it must not claim a stable matched-baseline result
until repeated seeds and natural history-value surface evals are run.

## Decision

```text
admit_m532_matched_short_train_single_seed
```
