# M143 Driver-Like Input Profile Audit

Date: 2026-05-22

## Source

This plan records the latest visible discussion in
`/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`.

The important correction is conceptual: a professional-driver-like RL policy
does not need explicit tire-state diagnostics to adapt. It should be allowed to
learn a capability latent from commands, actuator feedback, body response,
steering feel, scene geometry, and optionally raw vehicle proprioception.

## Updated Input Principle

Do not feed the deployable actor quantities that a driver would not directly
know and that require a vehicle-model diagnostic definition.

Keep out of the actor:

```text
slip_ratio
slip_angle
v_parallel_i as a required main-contract input
tire_force
normal_load
friction_circle_margin
ABS/TCS/ESC flag
mu
oracle feasibility
reference trajectory
path error / heading error / TTC
```

`v_parallel_i` can still be useful for logging, low-level fusion diagnostics,
probe targets, or an optional comparison profile. It should not be assumed as a
minimum actor input before the driver-like and raw-wheel profiles fail under the
same recipe.

## Profiles To Compare

### P0: Current Baseline

The current human-view recurrent frame:

```text
body response + actuator state + previous commands
road boundary points
obstacle geometry
optional obstacle rel-velocity zeroing for strict diagnostics
```

This keeps continuity with M62-M142.

### P1: Driver-Like Minimal

Response / self-ID branch:

```text
steer_cmd
brake_cmd
drive_cmd
actual_steering_angle
actual_brake_actuator_state
actual_drive_actuator_state
ax
ay
yaw_rate
steering_torque or EPS motor current
```

Scene branch:

```text
road boundary / drivable corridor
obstacle position in ego frame
obstacle size
```

This profile tests whether command-response mismatch plus steering feel and
scene geometry are enough to learn the handling envelope.

### P2: Driver-Like Minimal Without Steering Feel

Same as P1, but remove:

```text
steering_torque or EPS motor current
```

If P1 is clearly better than P2, steering feel is a high-value self-ID channel.
If P1 and P2 are similar, the current simulator may not yet make steering feel
meaningful enough to justify adding it.

### P3: Vehicle-Proprioception Minimal

P1 plus raw wheel speeds:

```text
wheel_speed_fl
wheel_speed_fr
wheel_speed_rl
wheel_speed_rr
```

Still do not add:

```text
v_parallel_i
slip_ratio
slip_angle
ABS/TCS/ESC flag
tire force
mu
```

This profile is less human-like but still deployable: production vehicles have
wheel-speed sensors. It tests whether raw wheel-speed history helps under
brake-lock-like, rear-spin, low-friction, or drift-onset conditions.

### P4: Optional Low-Level Fusion Comparison

P3 plus `v_parallel_i`:

```text
v_parallel_fl
v_parallel_fr
v_parallel_rl
v_parallel_rr
```

This is a comparison profile, not the default contract. It asks whether raw
commands, actuator feedback, IMU, steering feel, and wheel speed are
insufficient without local contact-patch ground-speed fusion.

If P4 gives only a small lift, keep it out of the main actor and use it for
diagnostics or privileged probe targets. If P4 is materially better, document
why the final deployable system requires a low-level fusion layer.

## Experiment Order

Use the same five-step reliability order already agreed for input studies:

```text
1. supervised information-observability probes
2. minimum-set sensor ablations
3. frozen-recipe RL profile comparison
4. matched hidden-dynamics wrong-history counterfactuals
5. optional-sensor admission gates
```

Do not tune PPO separately per profile. First find a stable training recipe,
then freeze:

```text
training budget
seeds
reward
curriculum
auxiliary losses
optimizer settings
evaluation corpus
gates
```

Only profile fields may change.

## Probe Targets

The target should be a future capability envelope, not `mu`:

```text
future braking deceleration
future yaw response
future lateral acceleration response
speed loss under brake pulse
yaw-rate response under steer pulse
stable AES feasibility
drift AES feasibility
AEB feasibility
recoverability after the maneuver
```

History windows:

```text
0.0 s
0.2 s
0.5 s
1.0 s
2.0 s
```

Expected evidence:

```text
history beats current frame on matched hidden-dynamics cases;
wrong history causes lower margin or wrong maneuver choice;
steering feel and/or raw wheel speed improves early envelope prediction only
when the simulator provides meaningful signal.
```

## Decision Boundary

The project should not claim "RL professional driver" from aggregate success
alone.

The stronger claim requires:

```text
high success and margin;
history ablation hurts on matched cases;
wrong history induces wrong capability assumptions;
the actor does not read hidden parameters, tire diagnostics, planner answers, or
oracle feasibility labels;
the chosen input profile wins under a frozen comparison recipe.
```

M142's `alpha_0_4` remains a guarded repair candidate for the current
observation branch. M143 is about deciding the next clean input branch before
more driver-level claims.

## Implemented Harness

New module:

```text
src/autodrift/driver_like_input_profile_audit.py
```

New tests:

```text
tests/test_driver_like_input_profile_audit.py
```

Audit config:

```text
configs/m143_driver_like_profile_audit.json
```

The current simulator cannot yet expose true steering torque/EPS current or
four-wheel independent sensing. Therefore this M143 run is explicitly scoped:

```text
steering feel: steer-rate proxy only
wheel speed: front/rear single-track proxy only
v_parallel: front/rear bicycle local ground-speed slots only
```

The exact per-frame feature profiles are written to:

```text
runs/m143_driver_like_input_profile_audit/profile_spec.csv
```

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_input_profile_audit \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 \
  --seed 9440 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m143_driver_like_input_profile_audit

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_input_profile_audit \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 \
  --seed 9441 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m143_driver_like_input_profile_audit_seed9441

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.driver_like_input_profile_audit \
  --env-config configs/m143_driver_like_profile_audit.json \
  --episodes 30 \
  --seed 9442 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m143_driver_like_input_profile_audit_seed9442
```

Multiseed summary:

```text
runs/m143_driver_like_input_profile_audit_multiseed/profile_delta_all_seeds.csv
runs/m143_driver_like_input_profile_audit_multiseed/profile_delta_multiseed_summary.csv
runs/m143_driver_like_input_profile_audit_multiseed/profile_delta_metric_summary.csv
runs/m143_driver_like_input_profile_audit_multiseed/summary.json
```

## Multiseed Aggregate

The table below aggregates over seeds `9440`, `9441`, and `9442`, targets
`future_braking_deceleration`, `future_yaw_response`, and
`future_lateral_accel_response`, and raw history windows `1`, `10`, and `25`.

| delta | mean test R2 delta | mean MAE-improvement delta |
| --- | ---: | ---: |
| P1 driver-like minimal - P0 current baseline | -0.086331 | 0.000510 |
| P1 steer-rate proxy - P2 no steering feel | -0.158046 | -0.023909 |
| P3 raw wheel - P1 driver-like minimal | 0.051552 | 0.006885 |
| P4 v_parallel - P3 raw wheel | 0.160504 | 0.032093 |

Target-window detail is in
`runs/m143_driver_like_input_profile_audit_multiseed/profile_delta_multiseed_summary.csv`.

## Interpretation

This is a supervised information audit, not PPO and not a driver promotion.

Findings:

- P1 does not stably beat P0. Removing `vx/vy` from the current baseline while
  keeping only command, actuator, IMU/yaw, steer-rate proxy, and scene geometry
  loses held-out R2 on average. Its mean MAE delta is near zero, so this is not a
  clean win or clean failure yet.
- The steer-rate proxy is not a valid substitute for steering torque/EPS
  current. P1 is worse than P2 on average, especially at longer raw windows.
- Raw front/rear wheel speed gives a small positive average lift, but the lift
  is noisy and target-dependent.
- Adding front/rear `v_parallel` gives the strongest supervised lift in this
  probe, especially for braking. This does not promote `v_parallel_i` to the
  actor contract because this is a single-track bicycle approximation and a
  linear supervised target, not closed-loop behavior evidence.

## Decision

M143 completes the first supervised input-profile audit and does not promote a
new actor observation profile.

Keep the current no-wheel human-view branch as the primary PPO-safe branch for
now. Keep raw wheel speed and `v_parallel` as experimental branches. Do not add
slip ratio, slip angle, controller flags, tire forces, `mu`, or oracle
feasibility labels.

The next task should be a learned-history repeat of the same P0-P4 profiles with
a frozen probe recipe. The question is whether the P3/P4 supervised ridge gains
survive regularized sequence modeling, or whether they are high-dimensional
linear artifacts.
