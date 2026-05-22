# M144 Driver-Like Learned-History Repeat

Date: 2026-05-22

## Question

M143 found that a supervised ridge probe gave a small/noisy positive lift for
raw wheel speed and a stronger positive lift for single-track `v_parallel`.
Before any PPO profile comparison, M144 asks whether those gains survive a
regularized learned-history sequence probe using the exact same P0-P4 feature
profiles.

## Method

New module:

```text
src/autodrift/driver_like_learned_history_probe.py
```

The probe reuses the exact per-frame feature indices from
`src/autodrift/driver_like_input_profile_audit.py`.

Profiles:

```text
P0 current no-wheel baseline
P1 driver-like minimal with steer-rate proxy
P2 P1 without steer-rate proxy
P3 P1 plus raw front/rear wheel speed
P4 P3 plus front/rear v_parallel
```

Frozen learned-history recipe:

```text
episodes: 40
seeds: 9450, 9451, 9452
policy: heuristic
horizon_steps: 15
sample_stride: 3
max_samples: 1000
history_window: 50
hidden_size: 24
epochs: 30
weight_decay: 0.001
device: cpu
```

Commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_learned_history_probe \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 \
  --seed 9450 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --history-window 50 \
  --hidden-size 24 \
  --epochs 30 \
  --weight-decay 0.001 \
  --device cpu \
  --run-dir runs/m144_driver_like_learned_history_seed9450

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_learned_history_probe \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 \
  --seed 9451 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --history-window 50 \
  --hidden-size 24 \
  --epochs 30 \
  --weight-decay 0.001 \
  --device cpu \
  --run-dir runs/m144_driver_like_learned_history_seed9451

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_learned_history_probe \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 \
  --seed 9452 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --history-window 50 \
  --hidden-size 24 \
  --epochs 30 \
  --weight-decay 0.001 \
  --device cpu \
  --run-dir runs/m144_driver_like_learned_history_seed9452
```

Artifacts:

```text
runs/m144_driver_like_learned_history_seed9450/summary.json
runs/m144_driver_like_learned_history_seed9451/summary.json
runs/m144_driver_like_learned_history_seed9452/summary.json
runs/m144_driver_like_learned_history_multiseed/summary.json
runs/m144_driver_like_learned_history_multiseed/profile_delta_all_seeds.csv
runs/m144_driver_like_learned_history_multiseed/profile_delta_multiseed_summary.csv
runs/m144_driver_like_learned_history_multiseed/profile_delta_metric_summary.csv
```

## Multiseed Aggregate

Aggregate over seeds `9450`, `9451`, `9452` and targets
`future_braking_deceleration`, `future_yaw_response`, and
`future_lateral_accel_response`:

| delta | mean test R2 delta | mean MAE-improvement delta |
| --- | ---: | ---: |
| P1 driver-like minimal - P0 current baseline | 0.002086 | -0.009776 |
| P1 steer-rate proxy - P2 no steering feel | -0.001224 | 0.003302 |
| P3 raw wheel - P1 driver-like minimal | -0.006285 | -0.004906 |
| P4 v_parallel - P3 raw wheel | -0.056911 | -0.021276 |

## Interpretation

M144 is a negative repeat for promoting P3 or P4.

The M143 ridge gains do not survive regularized sequence modeling:

- P1 and P0 are roughly tied in R2, but P1 loses MAE improvement on average.
- The steer-rate proxy remains non-evidence; it is not a substitute for true
  steering torque/EPS current.
- Raw front/rear wheel speed does not produce a learned-history lift.
- `v_parallel` is negative on average under the learned-history probe despite
  looking positive in M143 ridge.

This supports the concern that the M143 P4 result was a linear probe artifact or
target-specific low-level fusion shortcut, not a robust driver-like history
signal.

## Decision

Do not promote raw wheel speed or `v_parallel` into PPO profile comparison from
this evidence.

Keep the current no-wheel human-view branch as the PPO-safe branch. The next
input question should revisit whether "driver-like minimal" was too strict by
removing deployable speed/ego-kinematic cues that a real driver has through
speedometer and visual flow.
