# M81 Wheel Response Input Roadmap

Source: `~/workspace/AutoDrift - 项目评估分析.mhtml`, saved
2026-05-21 21:27 +0800.

This is the execution roadmap for the wheel/tire response branch. The broader
5.5pro MHTML review is preserved in
`docs/external-review-5-5pro-mhtml.md`.

## Decision

The MHTML review reframes the next major blocker as an input-and-evidence
problem, not only an objective-tuning problem.

Adopted interpretation:

- M80 remains the immediate short sanity check: prove
  `outcome_weighted_intervention_loss` can decrease outside PPO before spending
  more training time on that objective.
- After M80, the next larger infrastructure branch should be M81: add
  deployable wheel/tire response signals so the recurrent driver has a more
  realistic machine version of a skilled driver's tire feedback.
- The current 72-value human-view frame remains the comparison baseline, but it
  is not sufficient for the final self-identification claim.

The core claim should remain:

```text
RL proposes the maneuver from human-view scene plus action-response history.
A verifier or safety layer may check the proposed short action sequence.
The actor must not receive hidden friction, a reference path, or feasibility
labels.
```

## Why Wheel Response Matters

The current response stream covers body and actuator feedback:

```text
vx, vy, yaw_rate, ax, ay,
steer_angle, steer_rate,
throttle_state, brake_state,
prev_steer_cmd, prev_throttle_cmd, prev_brake_cmd
```

This is enough for a simplified simulator baseline, but it leaves important
ambiguities:

- weak deceleration could come from low friction, weak brake authority, wheel
  lock, or actuator lag;
- weak yaw response could come from low lateral authority, steering actuator
  lag, or front tire saturation;
- aggressive rear response could indicate drive-induced rear slip or drift
  onset.

Wheel-side signals reduce those ambiguities without giving oracle dynamics
parameters. They should be treated as deployable vehicle feedback, analogous to
the tire and chassis cues a skilled driver uses.

## Stage 1: Front/Rear Wheel Branch

For the current bicycle/single-track simulator, start with axle-level wheel
signals instead of a full four-wheel model:

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

Expected simple wheel dynamics:

```text
Iw * omega_dot_front = -T_brake_front - R * Fx_front
Iw * omega_dot_rear  =  T_drive_rear - T_brake_rear - R * Fx_rear
```

The slip proxy should be clipped, smoothed, delayed, and noisy enough to avoid
becoming a perfect simulator oracle:

```text
kappa_front = (R * omega_front - vx_front) / max(abs(vx_front), epsilon)
kappa_rear  = (R * omega_rear  - vx_rear)  / max(abs(vx_rear), epsilon)
```

## Stage 2: Four-Wheel Extension

If Stage 1 shows signal, extend to four-wheel response:

```text
wheel_speed_fl, wheel_speed_fr, wheel_speed_rl, wheel_speed_rr
wheel_accel_fl, wheel_accel_fr, wheel_accel_rl, wheel_accel_rr
slip_proxy_fl, slip_proxy_fr, slip_proxy_rl, slip_proxy_rr
front_avg_slip
rear_avg_slip
rear_minus_front_slip
left_right_slip_diff
```

This helps expose yaw-related tire behavior, left/right asymmetry, braking
asymmetry, and incipient spin.

## Stage 3: Control-System Proxies

Add deployable control-system feedback if the simulator supports it:

```text
actual_brake_pressure
commanded_brake_pressure
actual_drive_torque
commanded_drive_torque
steering_torque_or_motor_current
abs_active
tcs_active
esc_yaw_intervention
```

These signals may be visible to the actor because a real vehicle can know its
own actuator and stability-control states. They must not be implemented as
direct aliases for true friction, tire force limit, or oracle feasibility.

## Observation Placement

Wheel/tire response belongs in the response stream and recurrent self-ID
encoder:

```text
body + actuator + wheel response history -> response GRU / self-ID latent
road + obstacle scene geometry           -> context encoder
```

Do not put wheel response into the context branch. The context branch should
remain scene geometry and obstacle perception. The response branch should encode
what the vehicle did after the policy's commands.

## Not Actor Input

Do not add these to the deployable actor:

```text
true_mu
true tire stiffness
true brake scale
true actuator tau
true maximum tire force
true friction-circle utilization
ground-truth tire saturation label
AEB/AES/drift feasibility labels
required lateral offset
oracle stopping distance
reference trajectory
hidden speed_ref
hidden beta_target
```

They may still be used by teachers, offline probes, safety verifiers, corpus
miners, reward diagnostics, or baselines.

## Required M81 Gates

Do not judge the wheel branch by success rate alone. The proof target is
stronger self-identification evidence.

Compare profiles:

```text
A: current 72-value human-view frame
B: current + command-response error and response deltas
C: B + front/rear wheel response
D: B + four-wheel response
E: D + noisy and delayed sensors
```

For each profile, run:

```text
normal rollout
reset hidden
zero explicit response
zero wheel input
zero action history
wrong wheel-history injection
high-mu wheel history injected into low-mu episodes
low-mu wheel history injected into high-mu episodes
```

Expected pass evidence:

- normal margin and success do not regress versus the M62-class baseline after
  retention gates;
- zero wheel input degrades low-friction, brake-scale, and actuator-delay
  cases more than the current 72-value frame;
- wrong wheel history causes action or margin degradation on matched
  current-geometry/current-body-state cases;
- the recurrent latent predicts future handling-envelope targets better than a
  memoryless baseline.

Useful latent targets:

```text
future max braking decel
future max lateral acceleration
yaw authority
steering delay estimate
brake authority estimate
stable AES feasibility
drift AES feasibility
drift recoverability
```

## Immediate Ordering

Do not skip M80. The next two steps are:

```text
M80: prove the current outcome intervention loss is locally optimizable.
M81: add wheel/tire response inputs and wheel-specific self-ID gates.
```

If M80 fails, fix the objective/sign/data before more PPO. If M80 passes, M81
should still proceed because the MHTML review identifies wheel response as the
missing sensory channel for a professional-driver-like self-identification
claim.
