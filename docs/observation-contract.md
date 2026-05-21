# AutoDrift Observation Contract

Last updated: 2026-05-21

## Rule

The deployable RL actor should see the driving scene like a skilled driver or a
real perception stack: vehicle response, actuator feedback, recent commands,
road/free-space geometry in the ego frame, and obstacle geometry in the ego
frame.

The actor must not see hidden simulator parameters, oracle labels, controller
mode, path-tracking errors, target drift commands, or precomputed avoidance
answers.

`info` may still contain hidden values for logging, reward diagnostics,
benchmark buckets, and model-based baselines. `ActorPolicy` must not use
`info`.

Actor input/output contract changes invalidate old checkpoints. This project
does not keep observation-shape compatibility shims; the correct migration is a
new clean run.

## Current Actor Frame

The canonical human-view obstacle-driver frame has 72 values when
`history_length=1`, `action_history_mode="full"`,
`road_lookahead_count=8`, and `obstacle_slots=4`.

| index | value |
| ---: | --- |
| 0 | body-frame longitudinal velocity, `vx / 20` |
| 1 | body-frame lateral velocity, `vy / 12` |
| 2 | yaw rate, `yaw_rate / 2.5` |
| 3 | body-frame longitudinal acceleration, `ax / 15` |
| 4 | body-frame lateral acceleration, `ay / 15` |
| 5 | steering actuator angle, normalized by maximum steer |
| 6 | steering actuator rate, normalized by maximum steer rate |
| 7 | throttle actuator state in `[0, 1]` |
| 8 | brake actuator state in `[0, 1]` |
| 9 | previous steering command |
| 10 | previous throttle command in `[0, 1]` |
| 11 | previous brake command in `[0, 1]` |
| 12-27 | eight left road-boundary points in body frame, stored as `(x / 80, y / 20)` |
| 28-43 | eight right road-boundary points in body frame, stored as `(x / 80, y / 20)` |
| 44-71 | four obstacle slots, each `[present, x / 80, y / 20, vx / 20, vy / 12, half_width / 5, half_length / 5]` |

History is carried by the online GRU hidden state, not by stacking frames. The
current frame still includes the previous command because a driver knows what
they just asked the car to do.

Road input is not a reference path. It is an ego-frame free-space signal: where
the left and right road boundaries are ahead of the vehicle. Obstacle input is
object geometry and relative motion in the ego frame, not a precomputed
avoidance decision.

M67-D adds a stricter diagnostic profile through
`obstacle_relative_velocity_mode="zero"`. It keeps the 72-value shape and the
same obstacle slot layout, but sets the obstacle `vx` and `vy` channels to zero
for static-obstacle self-identification diagnostics. The default
`obstacle_relative_velocity_mode="ego"` preserves historical behavior.

## Not Actor Input

The policy observation must not include:

- `mu`, mass scale, CG shift, inertia scale, tire stiffness, brake scale, drive
  scale, or actuator time constants;
- `obstacle_label`;
- `aeb_stop_distance`;
- conventional-AES capacity, drift capacity, or any scenario feasibility label;
- friction-step timing or whether the friction step has already happened;
- `speed_ref`;
- `beta_target`;
- explicit sideslip angle `beta`;
- path lateral error;
- path heading error;
- path curvature;
- along-path speed;
- required lateral clearance;
- time to obstacle / TTC;
- reward terms, progress counters, collision labels, or success labels.

`include_privileged_params=True` remains a diagnostic or teacher-only option and
must not be used for deployable driver actors. Its default
`privileged_observation_mode="basic"` appends the legacy four-value packet:

```text
[mu, mass_scale, lf_scale, rear_tire_stiffness_scale]
```

M67-A adds `privileged_observation_mode="full_dynamics"` for upper-bound
teacher experiments only. It appends:

```text
[
  mu,
  mass_scale,
  inertia_scale,
  cg_shift / 0.25,
  front_tire_stiffness_scale,
  rear_tire_stiffness_scale,
  drive_scale,
  brake_scale,
  steer_tau_scale,
  drive_tau_scale,
]
```

The full packet is an oracle/teacher diagnostic. It must not be used by a
deployable driver actor or by any result claiming human-view control.

## Output Contract

The current simulator action is a three-dimensional normalized network command:

```text
[steering_command, throttle_command, brake_command]
```

The steering channel is normalized to `[-1, 1]`. The current PPO actor still
emits all action dimensions through a tanh head, so throttle and brake are
stored as normalized network commands in `[-1, 1]` and mapped inside the
environment to physical pedal positions:

```text
physical_throttle = 0.5 * (throttle_command + 1)
physical_brake = 0.5 * (brake_command + 1)
```

The observation reports the physical previous throttle and brake commands in
`[0, 1]`.

The desired next cleanup is to give PPO asymmetric action bounds so the actor
can directly emit throttle and brake in `[0, 1]`. That is a trainer-interface
cleanup, not a reason to keep the old combined drive/brake action.

Sequence-head experiments may predict a short action sequence and execute only
the first action before observing again. That remains a valid research branch,
but it does not change the deployed closed-loop contract.

## Reward And Baseline Boundary

`speed_ref`, `beta_target`, path error, and obstacle feasibility labels may
still exist inside the environment as reward, curriculum, diagnostic, or
model-baseline variables. They are not driver observations.

Hand-written baselines may read `info["mu"]`, `info["speed_ref"]`,
`info["beta_target"]`, `info["lateral_error"]`, or `info["obstacle_label"]`.
Those are model/oracle baselines, not deployable RL actors.

## Missing For A Better Driver

The next observation improvements should add deployable signals rather than
oracle labels:

- richer road/free-space polygons instead of two boundary polylines;
- multiple dynamic obstacle shapes and classes;
- wheel speeds, steering torque, brake pressure, and tire temperature if the
  simulator exposes them;
- camera/lidar/radar feature encoders once the structured human-view contract
  is working;
- asymmetric PPO action bounds for true `[steer, throttle, brake]` output.

## Wheel/Tire Response Branch

M81 adds `wheel_observation_mode="front_rear"` as a config-gated
self-identification input branch. It keeps the default 72-value frame unchanged,
and adds axle-level deployable response features to the response GRU stream only
when enabled:

```text
front_wheel_speed
rear_wheel_speed
front_wheel_accel
rear_wheel_accel
front_slip_proxy
rear_slip_proxy
rear_minus_front_slip
brake_pressure_front
brake_pressure_rear
drive_torque_rear
abs_front
abs_rear
tcs_active
```

That original M81 branch is a proxy wheel branch: the wheel-speed and slip slots
are derived from the single-track model's body state, drive force, and tire-force
residuals. It is useful for compatibility and historical M81-M88 comparisons,
but M91-B showed that it does not by itself justify PPO continuation as a clean
self-identification sensor.

M91-C adds `wheel_observation_mode="front_rear_raw"` as the cleaner minimum
wheel profile for new input-observability experiments. It preserves the same
13-slot shape and the same response-GRU placement, but exposes only simulated
front/rear wheel-speed state, wheel-speed acceleration, and physical actuator
pressure/torque slots. Derived slip and ABS/TCS proxy slots are zeroed:

```text
front_wheel_speed
rear_wheel_speed
front_wheel_accel
rear_wheel_accel
0.0
0.0
0.0
brake_pressure_front
brake_pressure_rear
drive_torque_rear
0.0
0.0
0.0
```

M91-H/M91-I found that learned response history is useful, but the current raw
wheel branch should not become the primary driver input: the no-wheel history
profile was better on braking and lateral response in the M91-I sensor
ablation. Keep `front_rear_raw` as an optional experimental sensor profile until
a later wheel model or corpus shows stable benefit over the no-wheel contract.

Important caveat: M91-I rejects the current single-track `front_rear_raw` proxy,
not the general idea of wheel-speed sensing. A stricter future wheel/tire
profile should expose the raw components of slip instead of slip diagnostics:

```text
Romega_i       = wheel circumferential speed
v_parallel_i  = independent local ground-speed estimate along the wheel rolling direction
```

For four-wheel simulation, this means per-wheel `Romega_fl/fr/rl/rr` and
`v_parallel_fl/fr/rl/rr`. Do not derive `v_parallel_i` from the average of wheel
speeds; that would erase the lockup/spin information the policy is supposed to
learn from. Optional future channels such as `v_perp_i`, steering torque, and
vertical dynamics require their own admission gates.

Do not put these diagnostic quantities into the actor:

```text
slip_ratio
slip_angle
ABS/TCS/ESC flags
tire_saturation_label
friction_circle_margin
```

See `docs/m92-local-wheel-ground-speed-input-plan.md` for the planned
observability audit.

With `action_history_mode="full"`, the Stage 1 wheel frame is:

```text
0-11   body response + previous commands
12-24  front/rear wheel response
25-84  road and obstacle context
```

These are allowed because they are vehicle feedback, not hidden environment
parameters. They must be noisy, delayed, clipped, or otherwise treated as
sensor-like estimates when needed. They must not become direct aliases for
`mu`, true tire force limits, true friction-circle utilization, saturation
labels, or AEB/AES/drift feasibility labels.

Wheel response should not be placed in the road/obstacle context branch:

```text
body + actuator + wheel response history -> recurrent self-ID encoder
road + obstacle geometry                 -> context encoder
```
