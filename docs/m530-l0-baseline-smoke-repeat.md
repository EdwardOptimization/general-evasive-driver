# M530 L0 Baseline Smoke Repeat

## Purpose

M530 repeats the L0 current-observation smoke from M528 on fresh seeds. This is
a route and metadata stability check only. It is not a baseline performance
comparison and does not promote a checkpoint.

## Commands

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m528_l0_current_observation_smoke.json \
  --device cpu \
  --seed 3530 \
  --run-dir runs/m530_l0_current_observation_smoke_seed3530

PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m528_l0_current_observation_smoke.json \
  --device cpu \
  --seed 3531 \
  --run-dir runs/m530_l0_current_observation_smoke_seed3531
```

## Results

Both runs completed `64` PPO steps with `2` envs and wrote checkpoints.

| Seed | Run Dir | Return Mean | Steps Mean | Termination Rate |
| --- | --- | ---: | ---: | ---: |
| 3530 | `runs/m530_l0_current_observation_smoke_seed3530` | `4.194043362873607` | `38.0` | `1.0` |
| 3531 | `runs/m530_l0_current_observation_smoke_seed3531` | `32.949701395277984` | `63.0` | `1.0` |

The return difference is not interpreted. The runs are too small and exist only
to verify repeatable plumbing.

## Metadata Check

For both runs:

```text
config.history_baseline.level = L0_current_observation
config.history_baseline.input_contract = P0_human_view_no_wheel_no_oracle
checkpoint.config.history_baseline_level = L0_current_observation
checkpoint.metadata.history_baseline.level = L0_current_observation
checkpoint.metadata.history_baseline.input_contract = P0_human_view_no_wheel_no_oracle
```

## Interpretation

M530 passes the process smoke repeat. The L0 route is stable enough to design a
matched short-train config family, but no trained-baseline evidence exists yet.

## Decision

```text
l0_smoke_repeat_pass_admit_m531_matched_short_train_config_design
```

Next blocker:

```text
m531-matched-history-short-train-config-design
```
