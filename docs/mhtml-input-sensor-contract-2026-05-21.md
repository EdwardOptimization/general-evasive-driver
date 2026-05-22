# MHTML Input Sensor Contract Extract

Source: `/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`.
Saved snapshot: 2026-05-21 23:50 +0800.

This note preserves the latest visible 5.5pro input discussion as an
implementation-facing contract. It is not a new experiment result. It is a
guardrail for future observation-profile work.

## 2026-05-22 Revision

The latest MHTML pass tightens the input philosophy again.

Earlier notes treated `Romega_i + v_parallel_i` as the minimum future wheel/tire
profile. The revised view is stricter and more driver-like:

```text
do not make v_parallel_i a required main actor input yet;
first test whether commands + actuator feedback + IMU + steering feel + scene
geometry can learn the available handling envelope;
then test raw wheel speeds as vehicle proprioception;
only then test v_parallel_i as an optional low-level fusion comparison.
```

The reason is that a skilled driver does not explicitly know tire slip ratio,
local tire-ground speed, tire force, or friction coefficient. The driver knows
the command they gave, feels actuator and steering response, senses body
acceleration/yaw, and sees the road/obstacle geometry. The RL latent should be
allowed to encode "what the car can currently do" from that closed-loop
evidence, instead of receiving a precomputed tire-state diagnostic.

The new profile ladder is recorded in
`docs/m143-driver-like-input-profile-audit.md`.

## Extracted Scope

The visible MHTML discussion contains the following important additions:

- actor inputs should be sensor-direct or minimally calibrated/fused;
- the actor should not receive engineered tire diagnostics, controller flags,
  hidden simulator parameters, planner answers, or oracle feasibility labels;
- the clean self-identification branch should preserve the closed-loop chain:

```text
known command
-> actual actuator feedback
-> wheel/contact raw response
-> body inertial response
-> road and obstacle geometry
```

The key correction from the latest exchange is stricter than the earlier
wheel-response plan: `slip_ratio` should not enter the actor even if it is
physically meaningful. Feed the raw components instead.

## Minimum Actor Inputs

Historical four-wheel strict profile from the previous MHTML pass:

```text
response / self-ID branch:
  commands:
    steer_cmd
    brake_cmd
    drive_cmd

  actual actuator feedback:
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

  body inertial response:
    ax
    ay
    yaw_rate

scene branch:
  road_boundary_points
  obstacle_present
  obstacle_x_ego
  obstacle_y_ego
  obstacle_width
  obstacle_length
```

`Romega_i` is the wheel circumferential speed. `v_parallel_i` is the local
contact-patch ground speed along the wheel rolling direction.

For the current single-track simulator, a temporary approximation may use:

```text
Romega_front
Romega_rear
v_parallel_front
v_parallel_rear
```

This approximation is not equivalent to a real four-wheel profile. It cannot
capture inside/outside wheel differences under large yaw rate or drift.

## Local Ground Speed Rule

Do not use vehicle-center speed as the denominator or ground-speed reference for
wheel slip. Do not estimate vehicle speed from the average of wheel speeds.

For wheel `i`, the local contact velocity in body coordinates is approximately:

```text
v_ix = vx - yaw_rate * y_i
v_iy = vy + yaw_rate * x_i
```

Then project onto that wheel's rolling direction:

```text
v_parallel_i =
  (vx - yaw_rate * y_i) * cos(delta_i)
  + (vy + yaw_rate * x_i) * sin(delta_i)
```

This matters most in emergency avoidance and drift because `vy`, `yaw_rate`,
wheel location, and steering angle can make each tire's local longitudinal
ground speed different.

`v_parallel_i` should come from independent low-level ego-motion fusion, such
as IMU/GNSS/RTK/visual odometry/radar odometry/kinematic constraints, with wheel
speed used only in trusted non-slip regions. This is still deployable low-level
fusion, not an oracle `mu` or feasibility label.

## Explicit Non-Inputs

Do not feed the deployable actor:

```text
slip_ratio
slip_angle
slip_proxy
ABS_active
TCS_active
ESC_active
per-wheel brake pressure split
tire_saturation_label
friction_circle_margin
true_tire_force
true_normal_load
mu
oracle feasibility
reference trajectory
```

These can be used for logging, probes, verifier targets, privileged teachers,
or corpus mining, but not for the policy input.

`slip_ratio` is excluded because it contains state-dependent division:

```text
(Romega_i - v_parallel_i) / v_parallel_i
```

That introduces low-speed singularities, sign switching, clipping and epsilon
choices, scale instability, and train/test distribution artifacts in lockup,
spin, reverse wheel-speed, and drift-onset cases.

If a wheel-speed difference is later tested, it should be a separate optional
affine feature:

```text
(Romega_i - v_parallel_i) / fixed_v_scale
```

This is not part of the minimum input set and must pass the same admission gates
as any optional sensor.

## Optional Sensors

Optional channels should be tested one group at a time:

```text
v_perp_fl/fr/rl/rr
steering_torque or EPS motor current
roll_rate, pitch_rate, vertical_acceleration
suspension_travel_fl/fr/rl/rr
road-surface perception embedding
sensor confidence or covariance
```

`v_perp_i` is useful for lateral slip, drift onset, and recoverability, but it
should remain optional until the low-level fusion quality and ablation evidence
are strong enough.

Steering torque/EPS current may expose front-tire aligning response earlier than
`steering_angle -> yaw_rate / ay` alone.

Roll/pitch/vertical acceleration and suspension travel may help under strong
load transfer, mass/cg randomization, or road variation. They should not be
added if the simulator lacks meaningful dynamics for those signals.

## Required Experiment Ladder

Use the input profiles in this order:

```text
A. supervised information-observability probes
B. minimum-set sensor ablations
C. frozen-recipe RL profile comparison
D. matched hidden-dynamics wrong-history counterfactuals
E. optional-sensor admission gates
```

Probe profiles:

```text
P0: no-wheel minimal
P1: minimum set with Romega and v_parallel
P2: P1 + steering torque or EPS current
P3: P1 + roll/pitch/vertical acceleration
P4: P1 + suspension travel
P5: P1 + all current optional sensors
```

Wheel-specific ablations:

```text
P1a: Romega only
P1b: Romega + v_parallel
P1c: Romega + v_parallel + v_perp
P1d: Romega + v_parallel + fixed-scale speed error
```

Do not add a `slip_ratio` profile to the main actor comparison. If it is ever
computed, keep it diagnostic-only unless there is a separate explicit negative
control.

The 2026-05-22 revision changes the first profiles to compare:

```text
P0: current baseline
P1: driver-like minimal
    commands + actuator actuals + IMU + steering torque/EPS current + scene
P2: driver-like minimal without steering torque/EPS current
P3: P1 + raw four-wheel speeds
P4: P3 + v_parallel_i as an optional low-level fusion comparison
```

This does not delete the old `Romega_i + v_parallel_i` plan; it demotes it from
"minimum future actor contract" to "optional comparison profile that must prove
it is needed."

## Probe Targets

Do not make `mu` the main target. Use future handling-envelope targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_acceleration_response
future_speed_loss_under_brake_pulse
future_yaw_rate_under_steer_pulse
stable_AES_feasibility
drift_AES_feasibility
AEB_feasibility
```

History windows should include:

```text
0.0 s
0.2 s
0.5 s
1.0 s
2.0 s
```

Expected self-identification evidence:

```text
current frame only is weaker;
0.5-1.0 s history improves future-envelope prediction;
wheel/local-ground-speed profiles improve earlier than no-wheel profiles if
the wheel signals are actually useful.
```

## Reliability Rule

Do not tune PPO independently for every input profile.

Reliable comparison sequence:

```text
1. reject clearly weak profiles through supervised probes;
2. find one stable PPO recipe on the strongest plausible profile;
3. freeze reward, curriculum, network size, auxiliary losses, seeds, budget,
   evaluation corpus, and gates;
4. train compared profiles under the same recipe;
5. iterate only from the best profile after the comparison is closed.
```

Paper-grade comparisons must keep configs, seeds, checkpoints, run artifacts,
probe summaries, ablation summaries, and decision notes. The comparison should
not be reconstructed from memory.

## Counterfactual Proof Standard

For driver-level self-identification, aggregate success is not enough. The
policy must show causal dependence on action-response history.

Important interventions:

```text
normal history
reset hidden
zero current response
zero all explicit response
zero action history
delayed history
action-response mismatch
wrong history from matched hidden dynamics
high-grip history injected into low-grip episode
low-grip history injected into high-grip episode
slow-actuator history injected into fast-actuator episode
fast-actuator history injected into slow-actuator episode
```

`wrong_history` is more convincing than `reset_hidden`: reset means "does not
know"; wrong history means "knows the wrong vehicle." A strong self-ID policy
should lose margin, choose the wrong timing, or suffer collision/mitigation
degradation when a matched but wrong response history is injected.

## Current AutoDrift Implication

M91/M92 do not admit the current single-track wheel profiles into the primary
PPO actor input. That negative result does not reject the future four-wheel
sensor contract above.

The active driver input remains the clean no-wheel human-view branch:

```text
body response + previous commands + actuator states + road/obstacle geometry
```

Future wheel work should proceed only after one of these is available:

```text
1. a real four-wheel or richer wheel-contact model;
2. a matched corpus where current body response is ambiguous but raw wheel /
   local-ground response changes the future-envelope target or wrong-history
   outcome.
```

This note reinforces `docs/m104-minimum-observable-input-contract.md` and should
be treated as the durable MHTML-derived input guardrail.
