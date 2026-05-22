# M146 Body-Feedback Observability Audit

Date: 2026-05-22

## Question

The latest MHTML discussion split the input question into two different
problems:

```text
1. passenger-like detection that the vehicle is already in a high-sideslip
   response state;
2. driver-like prediction of the future braking/yaw/lateral envelope before
   that response becomes obvious.
```

M146 tests those separately before returning to PPO. It is a supervised audit
only. It does not train or promote a driver checkpoint.

## Profiles

M146 uses the same 85-value wheel-response observation frame as M143/M145, but
the actor-like profile comparisons exclude non-deployable or diagnostic fields.

```text
passenger_body_response:
  yaw_rate, ax, ay

passenger_body_scene:
  yaw_rate, ax, ay, road boundary, obstacle geometry

h1_body_only:
  yaw_rate, ax, ay,
  steering actuator state,
  throttle/brake actuator states,
  previous steering/throttle/brake commands,
  road boundary, obstacle geometry

p0_current_baseline:
  current no-wheel human-view actor contract:
  vx, vy, yaw_rate, ax, ay,
  steering actuator state, steer-rate proxy,
  throttle/brake actuator states,
  previous steering/throttle/brake commands,
  road boundary, obstacle geometry
```

Excluded from all actor-like probe inputs:

```text
mu
slip ratio
v_parallel
tire force
TTC
path error
heading error
feasibility labels
required clearance
```

## Labels And Targets

Post-slip detection uses an offline label:

```text
post_slip := |beta| >= 0.06 rad
```

This is deliberately only a high-sideslip-tail proxy for the conservative
heuristic corpus. It is not a drift-angle success label and it is not supplied
to the actor-like probe input.

Pre-limit future-envelope prediction is run only on non-post-slip samples and
uses the existing targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

M146 also searches for ambiguous H1 body histories where H1 features are close
but future envelope targets are far apart.

## Implementation

New module:

```text
src/autodrift/body_feedback_observability_audit.py
```

New tests:

```text
tests/test_body_feedback_observability_audit.py
```

## Commands

Three seed runs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.body_feedback_observability_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --ridge 0.1 \
  --history-windows 1,10,25 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m146_body_feedback_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.body_feedback_observability_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --ridge 0.1 \
  --history-windows 1,10,25 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m146_body_feedback_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.body_feedback_observability_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --ridge 0.1 \
  --history-windows 1,10,25 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m146_body_feedback_seed9482
```

Aggregate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.body_feedback_observability_audit \
  --mode aggregate \
  --summary-jsons runs/m146_body_feedback_seed9480/summary.json,runs/m146_body_feedback_seed9481/summary.json,runs/m146_body_feedback_seed9482/summary.json \
  --run-dir runs/m146_body_feedback_multiseed
```

## Artifacts

```text
runs/m146_body_feedback_seed9480/summary.json
runs/m146_body_feedback_seed9481/summary.json
runs/m146_body_feedback_seed9482/summary.json
runs/m146_body_feedback_seed9480/ambiguous_body_history_pairs.csv
runs/m146_body_feedback_seed9481/ambiguous_body_history_pairs.csv
runs/m146_body_feedback_seed9482/ambiguous_body_history_pairs.csv
runs/m146_body_feedback_multiseed/summary.json
runs/m146_body_feedback_multiseed/aggregate_metric_summary.csv
```

## Sample Coverage

Across seeds `9480`, `9481`, and `9482`:

```text
post_slip samples:        122
pre_limit_nonpost samples: 2077
```

Ambiguous H1 body-history search found:

```text
seed 9480: 161 candidate pairs, 50 exported
seed 9481: 144 candidate pairs, 50 exported
seed 9482: 129 candidate pairs, 50 exported
total:    434 candidate pairs, 150 exported
```

## Multiseed Results

Post-slip detection deltas:

| Delta | Mean AUC delta | Mean balanced-accuracy delta |
| --- | ---: | ---: |
| passenger body+scene - body only | 0.166508 | 0.121409 |
| H1 - passenger body+scene | -0.027005 | -0.010327 |
| P0 - H1 | 0.014683 | 0.093991 |

Pre-limit future-envelope deltas over targets and history windows:

| Delta | Mean test R2 delta | Mean MAE-improvement delta |
| --- | ---: | ---: |
| passenger body+scene - body only | 0.014227 | -0.007046 |
| H1 - passenger body+scene | -0.044467 | -0.011010 |
| P0 - H1 | 0.004110 | 0.005291 |

## Interpretation

The post-slip result supports the passenger analogy in a narrow sense:
continuous body response plus scene geometry can identify high-sideslip-tail
states better than body response alone.

The driver-like H1 result is negative for pre-limit future-envelope prediction:
adding command intent and actuator state to body+scene does not reliably improve
future braking/yaw/lateral envelope prediction in this corpus. P0's additional
deployable `vx/vy` and steer-rate proxy give only a tiny average pre-limit lift.

The ambiguous-history search is the most important negative signal. There are
many cases where H1 body histories are close while future envelope targets
differ substantially. That means H1 may be information-limited for the exact
claim we want: early capability-envelope self-identification before obvious
sliding.

## Decision

Complete M146 as a negative/diagnostic input audit:

- do not promote H1 body-only as a replacement for the current P0 input;
- do not add wheel speed, `v_parallel`, slip ratio, or tire-force fields;
- do not restart PPO from a new input profile based on M146;
- keep P0 as the current deployable human-view baseline for now;
- future input work should test whether a genuinely driver-like steering-feel
  signal or other raw proprioception resolves the ambiguous H1 cases.
