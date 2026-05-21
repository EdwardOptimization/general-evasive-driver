# M67-C Input Profile Audit

This note records the 5.5pro observation/input-profile review and the adopted
project decision. It is intentionally separate from M67-A/B because it changes
the self-identification evidence standard, not just the teacher-training route.

## Decision

Keep the current 72-value human-view frame as the main deployable baseline, but
add stricter self-identification observation profiles before claiming
history-critical behavior.

Current score:

```text
deployable / human-view RL driver input: 7.5 / 10
self-identification proof input:        6.0 / 10
```

The current input is good enough for the main policy line. It is not clean enough
to make reset/zero-response ablations decisive evidence for online
self-identification.

## Current Profile

The canonical frame remains:

```text
0-8    ego response:
       vx, vy, yaw_rate, ax, ay, steer_angle, steer_rate,
       throttle_actuator_state, brake_actuator_state

9-11   previous physical commands:
       previous steer, previous throttle, previous brake

12-43  road boundary points:
       8 left + 8 right ego-frame boundary points

44-71  obstacle slots:
       4 slots x [present, x, y, rel_vx, rel_vy, half_width, half_length]
```

The `human_view_online_gru` split is still the right architecture direction:

```text
response/action stream 0-11 -> response_encoder -> GRUCell -> hidden
scene/context stream 12-71 -> context_encoder
policy feature = fusion(hidden, context, hidden * context)
```

This split is better than feeding the full observation into one generic GRU
because it makes recurrent state mainly carry action-response history while
keeping scene context current.

## What Is Correct

- The actor does not read `mu`, mass scale, tire stiffness, brake scale,
  actuator delay, obstacle labels, controller modes, path errors, TTC, target
  drift commands, or feasibility labels.
- Previous commands are necessary. Without them, the policy cannot distinguish
  "I did not ask for steering/braking" from "the car failed to respond".
- Road boundaries and obstacle geometry are ego-frame perception-like inputs,
  not precomputed controller answers.
- `history_length=1` with online GRU hidden state is correct for testing whether
  the actor stores history internally instead of relying on stacked-frame
  differencing.

## Main Weakness: Context Motion Proxies

The obstacle slots currently include:

```text
rel_vx = -ego_vx + yaw_rate * obstacle_body_y
rel_vy = -ego_vy - yaw_rate * obstacle_body_x
```

For static-obstacle tasks, these are essentially a second encoding of ego
velocity and yaw rate. This weakens response ablations:

```text
zero_current_response
zero_all_response
```

Those ablations clear explicit response indices 0-11, but obstacle relative
velocity can still leak part of `vx`, `vy`, and `yaw_rate` through the context
branch. If ablated policies remain strong, the result is ambiguous:

```text
possible interpretation A: response history is not needed
possible interpretation B: response is still available through context proxies
```

Road boundaries are also ego-frame and therefore contain pose-relative
information. That is legitimate perception input, but it means "zero response"
does not remove all state information.

## Adopted Profiles

### Profile A: Current Human-View Baseline

Keep:

```text
72-dim human_view_online_gru
response indices 0-11
context indices 12-71
obstacle slots include rel_vx / rel_vy
```

Purpose:

- preserve comparability with M37/M62/M65;
- remain the main deployable baseline;
- keep current checkpoint/gate history interpretable.

### Profile B: Strict Self-ID Context

Purpose:

- make self-identification diagnostics cleaner;
- reduce context-side motion proxies;
- test whether history interventions become more behavior-critical.

First implementation should not change observation dimension:

```text
obstacle slot stays 7 values
rel_vx = 0
rel_vy = 0
```

This preserves the 72-value shape while removing the static-obstacle velocity
proxy. If this profile is useful, a later cleaner variant can shrink slots to:

```text
[present, x, y, half_width, half_length]
```

Do not remove road boundaries in the first strict profile. Instead, add a
diagnostic ablation later if road-relative pose still masks response dependence.

### Profile C: Enhanced OSI Response

Purpose:

- make command-response identification easier for PPO;
- expose non-oracle actuator and vehicle response residuals;
- support an explicit OSI/dynamics-belief encoder.

Candidate response stream:

```text
vx
vy
yaw_rate
ax
ay
yaw_acceleration
steer_angle
steer_rate
throttle_state
brake_state
previous_steer_cmd
previous_throttle_cmd
previous_brake_cmd
steer_cmd_error
throttle_cmd_error
brake_cmd_error
delta_vx
delta_vy
delta_yaw_rate
command_delta_steer
command_delta_throttle
command_delta_brake
```

These are not hidden parameters or oracle labels. They are deployable
command-response features.

This profile will change observation dimension and actor constants, so it should
be introduced after Profile B validates the strict context direction.

### Profile D: Noisy IMU / Sensor Robustness

Purpose:

- prevent claims from depending on ideal, noiseless simulator acceleration;
- test whether self-ID survives realistic measurement imperfections.

Candidate perturbations:

```text
small noise on ax, ay, yaw_rate, steer_state
small delay on IMU/actuator state channels
small bias on ax/ay
```

Do not use noisy IMU as the first proof profile. First show clean strict-context
self-ID evidence, then stress it with noise.

## Reward Cleanup Risk

The observation correctly excludes:

```text
speed_ref
beta_target
```

However, the reward still uses hidden target terms:

```text
speed_cost = speed vs speed_ref
beta_cost = beta vs beta_target
```

This is a training-objective POMDP issue. The actor is punished for missing
targets it cannot observe. That was acceptable for early drift shaping, but it is
not ideal for an emergency-avoidance self-ID claim.

Future emergency reward cleanup should emphasize:

```text
collision
clearance margin
road boundary violation
spin / instability
control smoothness
progress through obstacle zone
recoverability after maneuver
```

If a target speed is needed, it should be a mission/planner input rather than a
hidden random reward variable.

## Inputs That Must Stay Out

Do not add these back to deployable actors:

```text
mu
mass_scale
tire_stiffness_scale
brake_scale
drive_scale
actuator_tau
obstacle_label
AEB feasible / AES feasible / drift_required
required lateral clearance
oracle stopping distance
path lateral error
path heading error
beta_target
friction-step flag
TTC
```

TTC is intentionally excluded for now. It can be perception-derived in real
systems, but in this research setting it risks becoming a precomputed timing
answer.

## Next Experiment: M67-D Strict Self-ID Profile

Implement a config-gated obstacle relative velocity mode:

```text
obstacle_relative_velocity_mode = "ego"   # current behavior
obstacle_relative_velocity_mode = "zero"  # strict self-ID context
```

Then add:

```text
configs/ppo_m67d_strict_self_id_context_driver.json
```

Initial smoke:

```text
train small strict-context recurrent policy
confirm observation stays 72 values
confirm obstacle rel_vx / rel_vy are zero
run benchmark/evaluate with normal and response ablations
```

Profile comparison matrix:

```text
current_72
current_72_no_obstacle_relvel
enhanced_response_no_obstacle_relvel
enhanced_response_noisy_imu_no_obstacle_relvel
```

Each profile should eventually run:

```text
normal
reset hidden
zero explicit response
zero action history
wrong matched history
delayed history
```

Pass signal:

```text
strict profiles preserve useful driving performance
and make wrong-history / zero-action-history / zero-response more harmful on
response-critical seeds
```

If strict context improves diagnostic sensitivity, keep it as the self-ID proof
profile. If performance collapses, keep current 72 as the main policy profile
and treat strict context as a diagnostic-only stress test.
