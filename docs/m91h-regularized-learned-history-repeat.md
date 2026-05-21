# M91-H Regularized Learned-History Repeat

M91-H repeats the learned history probe with a smaller GRU and stronger weight
decay across three seeds. The goal is to check whether M91-G's history signal is
repeatable or mostly single-seed overfit.

This is still not PPO and not a promoted driver.

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.learned_history_observability_probe \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 --seed 9370 --policy heuristic \
  --horizon-steps 15 --sample-stride 3 --max-samples 1000 \
  --history-window 50 --device cpu --epochs 30 --hidden-size 24 \
  --weight-decay 0.001 \
  --run-dir runs/m91h_learned_history_regularized_seed9370

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.learned_history_observability_probe \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 --seed 9371 --policy heuristic \
  --horizon-steps 15 --sample-stride 3 --max-samples 1000 \
  --history-window 50 --device cpu --epochs 30 --hidden-size 24 \
  --weight-decay 0.001 \
  --run-dir runs/m91h_learned_history_regularized_seed9371

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.learned_history_observability_probe \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 --seed 9372 --policy heuristic \
  --horizon-steps 15 --sample-stride 3 --max-samples 1000 \
  --history-window 50 --device cpu --epochs 30 --hidden-size 24 \
  --weight-decay 0.001 \
  --run-dir runs/m91h_learned_history_regularized_seed9372
```

Artifacts:

```text
runs/m91h_learned_history_regularized_seed9370/summary.json
runs/m91h_learned_history_regularized_seed9370/probe_summary.csv
runs/m91h_learned_history_regularized_seed9371/summary.json
runs/m91h_learned_history_regularized_seed9371/probe_summary.csv
runs/m91h_learned_history_regularized_seed9372/summary.json
runs/m91h_learned_history_regularized_seed9372/probe_summary.csv
```

## Mean Held-Out R2 Across Seeds

| profile | braking | yaw | lateral accel |
| --- | ---: | ---: | ---: |
| p0 current ridge | -0.109811 | 0.333512 | 0.301236 |
| p1 current ridge | -0.112906 | 0.337330 | 0.293977 |
| p0 response-history GRU | -0.014841 | 0.396916 | 0.300159 |
| p1 response-history GRU | -0.025442 | 0.391652 | 0.338666 |

## Per-Seed Direction

History versus current-frame ridge:

| target | p0 history improved seeds | p1 history improved seeds |
| --- | ---: | ---: |
| future braking decel | 3 / 3 | 3 / 3 |
| future yaw response | 3 / 3 | 2 / 3 |
| future lateral accel response | 1 / 3 | 2 / 3 |

P1 history versus P0 history:

| target | P1 better seeds |
| --- | ---: |
| future braking decel | 1 / 3 |
| future yaw response | 1 / 3 |
| future lateral accel response | 3 / 3 |

## Interpretation

M91-H is a qualified positive for learned history and still weak for wheel
necessity.

Positive:

- Smaller regularized GRU reduces the M91-G overfit problem.
- History improves braking and yaw relative to current-frame ridge in most or
  all seeds.
- P1 wheel history is best on mean lateral-response R2 and beats P0 history on
  lateral response in all three seeds.

Negative:

- Braking R2 remains weak in absolute terms.
- P1 wheel history is not stable on braking or yaw.
- The evidence supports "history matters" more strongly than "wheel speed is
  necessary."

## Decision

Do not unblock M90 PPO continuation yet.

Proceed to sensor ablation under the learned-history probe:

```text
M91-I: learned-history minimum-set sensor ablation.
```

The immediate question is now narrower:

```text
Which response channels explain the stable history benefit,
and why does the wheel branch help lateral response but not braking/yaw?
```
