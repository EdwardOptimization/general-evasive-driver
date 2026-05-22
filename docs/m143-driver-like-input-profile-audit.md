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
