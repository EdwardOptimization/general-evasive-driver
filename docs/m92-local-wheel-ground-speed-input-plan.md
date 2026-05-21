# M92 Local Wheel Ground-Speed Input Plan

This note records the latest input-design review from
`/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml` saved on
2026-05-21 23:50 +0800.

M92 does not reopen the rejected M91 `front_rear_raw` branch as the primary
driver input. It defines a stricter future wheel/tire observation profile that
must be tested separately.

## Core Correction

M91-I rejected the current `front_rear_raw` branch as a primary input. That
result should not be overread as "wheel speed is useless."

The rejected branch is still a single-track front/rear approximation. It does
not provide the physically correct per-wheel relation between:

```text
wheel circumferential speed
local wheel-contact ground speed
```

The newer input-design review argues that wheel/tire observability should use
those raw components rather than slip ratios or controller flags.

## Minimum Observable Actor Set

The latest review refines the deployable minimum set as:

```text
known commands:
  steering command
  brake command
  drive/throttle command

actual actuator feedback:
  steering rack / road-wheel angle
  brake actuator or line-pressure state
  drive actuator / motor-current / throttle state

wheel raw:
  Romega_fl
  Romega_fr
  Romega_rl
  Romega_rr

local ground-speed fusion:
  v_parallel_fl
  v_parallel_fr
  v_parallel_rl
  v_parallel_rr

body inertial response:
  ax
  ay
  yaw_rate

scene:
  road boundary / drivable corridor
  obstacle present
  obstacle ego-frame position
  obstacle size
```

The key correction is replacing a single `vehicle_speed_fused` with local
contact-patch ground speeds. For handling-limit avoidance, the center speed is
not enough: yaw rate, lateral velocity, wheel position, and front steering angle
make each tire's local longitudinal ground speed different.

Current AutoDrift still exposes `vx` and `vy` in the 72-value baseline frame.
M92 treats local ground speed as an additional low-level fused wheel-contact
signal for experiment profiles, not as a hidden simulator parameter or an
oracle feasibility label.

## Do Not Input Slip Ratio

Do not feed actor:

```text
slip_ratio
slip_angle
wheel_slip_label
tire_saturation_label
friction_circle_margin
ABS/TCS/ESC flags
true_tire_force
true_mu
```

Even if slip ratio is physically meaningful, it is a diagnostic feature with
division:

```text
(R * omega - v_parallel) / v_parallel
```

That creates low-speed singularity, epsilon/clip choices, sign switching, and
distribution artifacts. It is suitable for logging, probes, verifier targets,
or teacher diagnostics, but not for the deployable actor input.

## Correct Raw Components

For each wheel `i`, the clean actor-facing components are:

```text
Romega_i       = R_i * omega_i
v_parallel_i  = local contact-patch ground speed along the wheel rolling direction
```

Optional later component:

```text
v_perp_i       = local contact-patch ground speed perpendicular to the wheel plane
```

The recurrent actor can infer tire state from the history of these components
plus commands, actuator state, IMU response, and scene context.

## Vehicle Speed Must Not Come From Wheel-Speed Average

Do not estimate vehicle speed as:

```text
mean(Romega_fl, Romega_fr, Romega_rl, Romega_rr)
```

Wheel speed is the signal used to detect lockup, spin, and drift onset. Using
wheel speed itself to define the ground speed reference washes out the slip
information and creates a circular definition.

`v_parallel_i` should come from independent low-level ego-motion fusion, such
as:

```text
IMU integration/fusion
GNSS/RTK
visual odometry
radar odometry
vehicle kinematic constraints
wheel speed only in trusted non-slip regions
```

This is still deployable low-level fusion, not an oracle `mu` or feasibility
label.

## Four-Wheel Profile

Strict future four-wheel response branch:

```text
commands:
  steer_cmd
  brake_cmd
  drive_cmd

actuator actuals:
  actual_steering_angle
  actual_brake_actuator_state
  actual_drive_actuator_state

wheel raw:
  Romega_fl
  Romega_fr
  Romega_rl
  Romega_rr

local ground-speed fusion:
  v_parallel_fl
  v_parallel_fr
  v_parallel_rl
  v_parallel_rr

body inertial:
  ax
  ay
  yaw_rate

scene:
  road_boundary_points
  obstacle_present
  obstacle_x_ego
  obstacle_y_ego
  obstacle_width
  obstacle_length
```

Optional future channels:

```text
v_perp_fl/fr/rl/rr
steering_torque / EPS current
roll / pitch / vertical acceleration
suspension travel
```

## Bicycle Approximation

If the simulator is still single-track, the temporary approximation should be:

```text
Romega_front
Romega_rear
v_parallel_front
v_parallel_rear
```

For a bicycle front axle:

```text
v_parallel_front =
  vx * cos(steer) + (vy + yaw_rate * lf) * sin(steer)
```

For a bicycle rear axle:

```text
v_parallel_rear = vx
```

This is still only a temporary approximation. A four-wheel model is needed to
capture yaw-induced inside/outside wheel differences.

## M92 Experiment Profiles

Do not test slip ratio as a main actor profile.

Recommended M92 probe profiles:

```text
P0: no-wheel learned-history baseline
P1: Romega only
P2: Romega + v_parallel
P3: Romega + v_parallel + v_perp
P4: Romega + v_parallel + fixed-scale speed error
```

The current single-track implementation can only test:

```text
P1: front_rear_omega
P2: front_rear_omega_ground
P4: front_rear_omega_ground_error
```

`P3` remains a future four-wheel or richer state-estimator profile because the
bicycle simulator does not provide meaningful per-wheel lateral contact speed.

`P4` may use:

```text
(Romega_i - v_parallel_i) / fixed_v_scale
```

This is an affine difference with a fixed normalization scale, not a slip ratio
with a state-dependent denominator. It should be treated as optional and only
kept if it improves stability or learning speed without weakening the final
self-identification evidence.

## Gate Questions

M92 must answer:

```text
1. Does Romega + v_parallel improve future braking/yaw/lateral envelope probes?
2. Does the learned-history encoder benefit more from local wheel signals than
   from the rejected M91 front/rear raw proxy?
3. Does the wheel profile improve wrong-history counterfactual sensitivity?
4. Does it remain stable in low-speed, lockup, and drift-onset samples?
```

If these gates fail, keep the no-wheel human-view response stream as the primary
driver input.

If they pass, the wheel/local-ground-speed profile can re-enter the PPO-facing
profile comparison.

## Current Implementation Constraint

The M92 single-track approximation keeps the historical 13-slot wheel branch so
existing wheel-response encoders and probe harnesses stay comparable:

```text
0   Romega_front / 20
1   Romega_rear / 20
2   v_parallel_front / 20, or 0 for Romega-only
3   v_parallel_rear / 20, or 0 for Romega-only
4   fixed-scale front speed error, only in P4
5   fixed-scale rear speed error, only in P4
6   0
7   brake actuator state, front proxy
8   brake actuator state, rear proxy
9   drive actuator state, rear proxy
10  0
11  0
12  0
```

The fixed-scale error is:

```text
(Romega_i - v_parallel_i) / 20
```

It is deliberately not a slip ratio because the denominator is a constant
normalization scale, not the current local ground speed.
