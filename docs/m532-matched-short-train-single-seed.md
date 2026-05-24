# M532 Matched Short-Train Single Seed

## Purpose

M532 runs the matched L0/L2/L3 short-train configs from M531 on the shared seed
`3530`. This is a route and artifact gate. It checks that all three baseline
families can train under the same budget and write comparable artifacts.

This is not a stable baseline ranking and does not promote a checkpoint.

## Commands

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

## Results

All three runs completed `1024` PPO steps.

| Level | Run Dir | Return Mean | Steps Mean | Termination Rate |
| --- | --- | ---: | ---: | ---: |
| L0 current observation | `runs/m532_matched_l0_short_train_seed3530` | `15.87732169255949` | `51.2` | `1.0` |
| L2 finite window | `runs/m532_matched_l2_short_train_seed3530` | `15.247255288372685` | `50.8` | `1.0` |
| L3 online GRU | `runs/m532_matched_l3_short_train_seed3530` | `43.47362037114112` | `55.0` | `0.6` |

L3 is better on this single seed and eval sample, but this is only a route
check. The result must be repeated across seeds and evaluated on natural
history-value surfaces before any claim about recurrent-history value.

## Metadata Check

For each run:

```text
config.history_baseline.level matches the declared level
checkpoint.config.history_baseline_level matches the declared level
checkpoint.metadata.history_baseline.level matches the declared level
checkpoint.metadata.history_baseline.input_contract = P0_human_view_no_wheel_no_oracle
```

## Interpretation

M532 passes the single-seed matched short-train route gate. The next step should
repeat the same frozen configs on fresh seeds without tuning any one baseline
after seeing the M532 result.

## Decision

```text
matched_short_train_single_seed_pass_admit_m533_repeat_seed
```

Next blocker:

```text
m533-matched-short-train-repeat-seeds
```
