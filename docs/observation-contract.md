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
must not be used for deployable driver actors.

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
