# M533 Matched Short-Train Repeat Seeds

## Purpose

M533 repeats the frozen M531 L0/L2/L3 short-train configs on fresh seeds
`3531` and `3532`, and aggregates them with the M532 seed `3530` run. The goal
is route stability and preliminary multi-seed direction, not promotion or
paper-level evidence.

No config was tuned after seeing M532.

## Commands

For seed `3531`:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l0_short_train.json --device cpu --seed 3531 --run-dir runs/m533_matched_l0_short_train_seed3531
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l2_short_train.json --device cpu --seed 3531 --run-dir runs/m533_matched_l2_short_train_seed3531
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l3_short_train.json --device cpu --seed 3531 --run-dir runs/m533_matched_l3_short_train_seed3531
```

For seed `3532`:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l0_short_train.json --device cpu --seed 3532 --run-dir runs/m533_matched_l0_short_train_seed3532
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l2_short_train.json --device cpu --seed 3532 --run-dir runs/m533_matched_l2_short_train_seed3532
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo --config configs/ppo_m531_matched_l3_short_train.json --device cpu --seed 3532 --run-dir runs/m533_matched_l3_short_train_seed3532
```

## Per-Seed Results

| Seed | Level | Return Mean | Steps Mean | Termination Rate |
| --- | --- | ---: | ---: | ---: |
| 3530 | L0 current observation | `15.87732169255949` | `51.2` | `1.0` |
| 3530 | L2 finite window | `15.247255288372685` | `50.8` | `1.0` |
| 3530 | L3 online GRU | `43.47362037114112` | `55.0` | `0.6` |
| 3531 | L0 current observation | `35.51390868136426` | `55.6` | `0.8` |
| 3531 | L2 finite window | `73.05600879656586` | `62.6` | `0.2` |
| 3531 | L3 online GRU | `37.96579930833953` | `57.0` | `0.8` |
| 3532 | L0 current observation | `30.51367562202102` | `49.6` | `0.8` |
| 3532 | L2 finite window | `31.42128828262816` | `49.6` | `0.8` |
| 3532 | L3 online GRU | `55.89002523848313` | `54.6` | `0.4` |

## Aggregate Summary

| Level | Return Mean Avg | Termination Rate Avg | Metadata |
| --- | ---: | ---: | --- |
| L0 current observation | `27.30163533198159` | `0.8666666666666667` | all OK |
| L2 finite window | `39.908184122522236` | `0.6666666666666667` | all OK |
| L3 online GRU | `45.77648163932126` | `0.6` | all OK |

## Interpretation

The route is stable: all nine short-train runs completed and wrote correct
`history_baseline` metadata.

The preliminary direction is consistent with history helping, but still not
strong evidence:

```text
L3 has the best 3-seed average return and termination rate.
L2 wins seed 3531.
L3 wins seeds 3530 and 3532.
L0 is not catastrophically broken.
```

This should not be promoted or claimed as final because the budget is tiny,
eval episodes are few, and the result has not been checked on natural
history-value surfaces.

## Decision

```text
matched_short_train_repeat_pass_admit_m534_natural_surface_eval_design
```

Next blocker:

```text
m534-matched-history-natural-surface-eval-design
```
