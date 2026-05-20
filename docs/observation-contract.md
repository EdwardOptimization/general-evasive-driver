# AutoDrift Observation Contract

Last updated: 2026-05-21

## Rule

The actor observation must be deployable. It may contain sensed or estimated
vehicle response, localization/perception outputs, route or free-space geometry,
actuator state, and recent commands. It must not contain hidden simulator
parameters, oracle feasibility labels, policy targets generated from hidden
physics, or hand-engineered drift commands.

`info` may still contain hidden values for logging, reward diagnostics,
benchmark buckets, and model-based baselines. `ActorPolicy` must not use
`info`.

Actor input/output contract changes invalidate old checkpoints. This project
does not keep observation-shape compatibility shims; the correct migration is a
new clean run.

Checkpoint loading is also strict. Saved checkpoints must explicitly declare
the actor encoder, actor history length, sequence horizon, response-prediction
dimension, and log-std bounds in their config. The loader must fail on missing
model-contract fields instead of inferring them from old weight shapes.

The only supported action-history modes are `full` and `none`. The clean driver
default is `full`, which exposes both previous steering and previous
drive/brake command. The old one-channel action-history mode is removed.

## Current Actor Frame

The canonical obstacle-driver frame has 15 values when
`action_history_mode="full"`:

| index | value |
| ---: | --- |
| 0 | body-frame longitudinal velocity, `vx / 20` |
| 1 | body-frame lateral velocity, `vy / 12` |
| 2 | yaw rate, `yaw_rate / 2.5` |
| 3 | steering actuator state, normalized by maximum steer |
| 4 | drive/brake actuator state, normalized by maximum force |
| 5 | lateral path error, normalized by track width |
| 6 | heading error |
| 7 | current path curvature, scaled by 20 |
| 8 | along-path speed, divided by 20 |
| 9 | previous steering command |
| 10 | previous drive/brake command |
| 11 | obstacle longitudinal distance, divided by 80 |
| 12 | obstacle lateral offset, normalized by track width |
| 13 | required lateral clearance, normalized by track width |
| 14 | time to obstacle, divided by 5 |

With `history_length=4`, the current clean driver observation dimension is 60.
History is ordered current frame first, then older frames.

`vx` and `vy` are vehicle response components, not a precomputed sideslip angle.
If a future real-car stack cannot estimate lateral velocity well enough, replace
these with deployable IMU, wheel-speed, visual-inertial, or state-estimator
signals. Do not add a simulator-only sideslip feature.

## Not Actor Input

The policy observation must not include:

- `mu`, mass scale, CG shift, tire stiffness, brake scale, drive scale, or
  actuator time constants;
- `obstacle_label`;
- `aeb_stop_distance`;
- conventional-AES capacity, drift capacity, or any scenario feasibility label;
- friction-step timing or whether the friction step has already happened;
- `speed_ref`;
- `beta_target`;
- explicit sideslip angle `beta`;
- reward terms, progress counters, collision labels, or success labels.

`include_privileged_params=True` remains a diagnostic or teacher-only option and
must not be used for deployable driver actors.

## Output Contract

The current simulator action is two-dimensional:

```text
[steering_command, drive_brake_command]
```

Both channels are normalized to `[-1, 1]`. The second channel is positive for
drive/throttle and negative for braking. The actor directly controls the vehicle
at the current time step.

Sequence-head experiments may predict a short action sequence and execute only
the first action before observing again. That is a valid research branch, but it
does not change the deployed closed-loop contract.

The desired hardware-facing contract should eventually split throttle and brake
into separate channels. If that action contract changes, old policies must be
retrained under the new contract.

## Reward And Baseline Boundary

`speed_ref` and `beta_target` may still exist inside the environment as reward
or curriculum variables. They are not driver observations.

Hand-written baselines may read `info["mu"]`, `info["speed_ref"]`,
`info["beta_target"]`, or `info["obstacle_label"]`. Those are model/oracle
baselines, not deployable RL actors.

## Missing For A Better Driver

The next observation improvements should add deployable signals rather than
oracle labels:

- lookahead path curvature or local path points instead of only current
  curvature;
- lane, road-boundary, and obstacle free-space representation;
- obstacle velocity and acceleration for dynamic obstacles;
- separate throttle and brake command/state instead of one combined
  drive/brake scalar;
- IMU acceleration, wheel speeds, steering rate, brake pressure, and actuator
  feedback if the simulator exposes them;
- carried recurrent hidden state with hidden-state reset ablation at validation
  time.
