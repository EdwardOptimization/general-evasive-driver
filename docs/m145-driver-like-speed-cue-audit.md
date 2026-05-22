# M145 Driver-Like Speed-Cue Audit

Date: 2026-05-22

## Question

M143/M144 showed that the narrower P1 driver-like minimal profile did not
reliably beat the current P0 human-view baseline. M145 asks whether P1 was too
strict because it removed deployable ego-speed cues that a real driver or
perception stack would have.

This is an input audit only. It does not train PPO and does not promote a new
driver checkpoint.

## Profiles

M145 reuses the M143 observation frame and adds only deployable ego-kinematic
cues:

```text
P0 current no-wheel baseline
P1 driver-like minimal without explicit speed cue
P5 P1 + vx
P6 P1 + vx/vy
```

Important equivalence:

```text
P6 = P0
```

P0 contains `vx`, `vy`, `yaw_rate`, IMU-like acceleration, actuator states,
previous commands, and road/obstacle geometry. P6 reconstructs the same feature
set by adding `vx/vy` back to P1.

These fields remain excluded:

```text
path error
heading error
TTC
required clearance
feasibility labels
mu
slip ratio
slip angle
tire force
controller mode
```

## Implementation

New module:

```text
src/autodrift/driver_like_speed_cue_audit.py
```

New tests:

```text
tests/test_driver_like_speed_cue_audit.py
```

## Commands

Ridge seeds:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode ridge --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 --seed 9460 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 800 --ridge 0.1 --history-windows 1,10,25 \
  --run-dir runs/m145_speed_cue_ridge_seed9460

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode ridge --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 --seed 9461 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 800 --ridge 0.1 --history-windows 1,10,25 \
  --run-dir runs/m145_speed_cue_ridge_seed9461

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode ridge --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 --seed 9462 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 800 --ridge 0.1 --history-windows 1,10,25 \
  --run-dir runs/m145_speed_cue_ridge_seed9462
```

Learned-history seeds:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode learned --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9470 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 50 --hidden-size 24 \
  --epochs 30 --weight-decay 0.001 --device cpu \
  --run-dir runs/m145_speed_cue_learned_seed9470

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode learned --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9471 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 50 --hidden-size 24 \
  --epochs 30 --weight-decay 0.001 --device cpu \
  --run-dir runs/m145_speed_cue_learned_seed9471

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_speed_cue_audit \
  --mode learned --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9472 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --history-window 50 --hidden-size 24 \
  --epochs 30 --weight-decay 0.001 --device cpu \
  --run-dir runs/m145_speed_cue_learned_seed9472
```

## Artifacts

```text
runs/m145_speed_cue_ridge_seed9460/summary.json
runs/m145_speed_cue_ridge_seed9461/summary.json
runs/m145_speed_cue_ridge_seed9462/summary.json
runs/m145_speed_cue_ridge_multiseed/summary.json
runs/m145_speed_cue_ridge_multiseed/profile_delta_metric_summary.csv
runs/m145_speed_cue_learned_seed9470/summary.json
runs/m145_speed_cue_learned_seed9471/summary.json
runs/m145_speed_cue_learned_seed9472/summary.json
runs/m145_speed_cue_learned_multiseed/summary.json
runs/m145_speed_cue_learned_multiseed/profile_delta_metric_summary.csv
```

## Multiseed Results

Ridge aggregate over seeds `9460`, `9461`, `9462`, targets, and history windows:

| delta | mean test R2 delta | mean MAE-improvement delta |
| --- | ---: | ---: |
| P1 - P0 | -0.197442 | -0.042090 |
| P5 vx - P1 | 0.065391 | 0.015470 |
| P6 vx/vy - P1 | 0.197442 | 0.042090 |
| P6 - P0 | 0.000000 | 0.000000 |

Learned-history aggregate over seeds `9470`, `9471`, `9472`:

| delta | mean test R2 delta | mean MAE-improvement delta |
| --- | ---: | ---: |
| P1 - P0 | -0.006595 | -0.005549 |
| P5 vx - P1 | -0.005735 | -0.001383 |
| P6 vx/vy - P1 | -0.008342 | 0.002861 |
| P6 - P0 | -0.014937 | -0.002688 |

For learned-history, P6 and P0 use the same feature set but train separate GRU
models with different initializations. Their nonzero deltas are training noise,
not input differences.

## Interpretation

M145 confirms that the current P0 baseline is not an oracle shortcut. Its `vx`
and `vy` channels are deployable ego-kinematic cues, closer to speedometer,
inertial odometry, and visual-flow state than to planner answers.

The narrow P1 profile should not replace P0:

- in ridge, P1 is clearly below P0 on average;
- adding only `vx` helps in ridge but does not survive learned-history;
- adding `vx/vy` reconstructs P0 exactly;
- learned-history results are close/noisy and do not justify a new profile.

## Decision

Do not create a new speed-cue actor profile.

Keep the current no-wheel human-view baseline as the primary PPO-safe input:

```text
vx
vy
yaw_rate
ax
ay
steering actuator state
throttle/brake actuator state
previous physical commands
road/obstacle geometry
```

Do not promote raw wheel, `v_parallel`, or the narrower P1 profile.

The latest MHTML update after this run adds an important caveat: before
returning to PPO, split the input question into passenger-like detection of
already-visible sliding and driver-like prediction of future handling envelope.
The next step should therefore be a body-feedback observability audit, not PPO.
See `docs/mhtml-body-feedback-input-revision-2026-05-22.md`.
