# MHTML Body-Feedback Input Revision

Source: `/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`

Read time: 2026-05-22

## Core Distinction

The latest MHTML discussion separates two problems that should not be conflated:

```text
1. detecting that sliding / loss of control is already happening;
2. predicting how much future braking, yaw, and lateral authority remains before
   the maneuver is fully committed.
```

Passenger-like sensing can often detect the first problem from continuous body
feedback:

```text
ax(t)
ay(t)
yaw_rate(t)
jerk
roll / pitch
visual flow
seat pressure
vibration / sound
```

But emergency avoidance requires the second problem: the policy must infer the
current capability envelope early enough to decide whether to brake, perform
stable AES, induce/accept drift, or mitigate an unavoidable collision.

## Driver-Like Self-ID Chain

Wheel speed, slip ratio, local tire ground speed, tire force, and `mu` are not
required preconditions for perceiving sliding. A driver-like policy should first
be tested with the closed-loop chain:

```text
command history
actual actuator state history
continuous ax / ay / yaw_rate history
road and obstacle geometry history
```

This is stronger than passenger sensing because the driver knows control intent:

```text
I asked for this steer/brake/drive command;
the actuators reached this state;
the vehicle body responded this way;
therefore the available handling envelope is likely this.
```

## Input Hypotheses

### H1: Body-Only

Most important baseline:

```text
commands:
  steer_cmd
  brake_cmd
  drive_cmd

actuator actuals:
  actual_steering_angle
  actual_brake_actuator_state
  actual_drive_actuator_state

body response:
  ax
  ay
  yaw_rate

scene:
  road boundary / drivable corridor
  obstacle position and size
```

Question:

```text
Can command intent + actuator state + continuous body inertial feedback support
self-identifying emergency avoidance?
```

If H1 succeeds, the claim is strong: explicit wheel/tire variables are not
needed for the driver-like latent.

### H2: Driver Feel

Add steering/front-end feel:

```text
steering_torque
EPS_motor_current
steering_rack_force_proxy
```

Question:

```text
Is steering feel the key early signal for front grip, understeer, or lateral
force buildup?
```

This is more driver-like than wheel-speed sensing.

### H3: Vehicle Proprioception

Add raw vehicle sensors without diagnostic ratios:

```text
raw wheel_speed_fl
raw wheel_speed_fr
raw wheel_speed_rl
raw wheel_speed_rr
```

Still excluded:

```text
slip ratio
v_parallel
ABS/TCS/ESC flag
tire force
normal load
mu
friction circle
oracle feasibility
```

Question:

```text
Do raw wheel-speed sensors reveal useful self-ID information beyond body and
steering feel?
```

## Required Experiments

### 1. Body-Only Envelope Probe

Before RL, compare future-envelope prediction from:

```text
P1: body-only
P2: body-only + steering torque / EPS
P3: body-only + steering torque / EPS + raw wheel speed
P4: body-only + roll/pitch/vertical acceleration
P5: all allowed sensors
```

Use history lengths:

```text
current frame
0.2 s
0.5 s
1.0 s
2.0 s
```

Targets:

```text
future brake response
future yaw response
future lateral acceleration response
stable AES feasibility
drift AES feasibility
recoverability
```

### 2. Pre-Slip vs Post-Slip Split

Split samples into:

```text
pre-slip / pre-limit:
  no obvious sliding yet, but future maneuver approaches handling limit

post-slip / at-limit:
  sliding or instability response is already visible
```

Expected pattern:

```text
post-slip: body-only may be strong;
pre-slip: body-only may be weaker, and steering feel or wheel speed may matter.
```

This directly addresses the passenger analogy: passengers can feel sliding after
it becomes visible, but drivers need to act before the failure is obvious.

### 3. RL Profile Comparison

Only after probes, train profile-matched policies with frozen settings:

```text
same PPO budget
same seeds
same reward
same curriculum
same network size
same evaluation corpus
```

Evaluate:

```text
success rate
clearance margin
collision / spin rate
held-out hidden dynamics
wrong-history gap
reset-hidden gap
zero-IMU-history gap
delayed-history gap
```

### 4. Passenger-Style Slip Detection

Probe whether continuous body response alone can detect current sliding:

```text
input:
  ax(t-k:t)
  ay(t-k:t)
  yaw_rate(t-k:t)
  optional road/obstacle visual geometry history

excluded:
  commands
  actuators
  wheel speed
  steering torque
```

Labels may be generated offline from the simulator, but must not enter the
actor.

This separates:

```text
passenger-like sensing: detect current sliding;
driver-like sensing: predict response to intended actions.
```

### 5. Ambiguous History Search

Search for matched pairs where:

```text
body-only command + actuator + ax/ay/yaw history is close
future envelope is different
```

Then test whether the ambiguity is resolved by:

```text
steering torque / EPS
raw wheel speed
roll/pitch
suspension feedback
```

This asks whether a profile is information-theoretically insufficient before
spending PPO budget.

## Updated Direction

The project should not jump from M145 directly back to PPO. The next high-value
step is a body-feedback observability audit that distinguishes:

```text
already-sliding detection
pre-limit future capability prediction
ambiguous body-history cases
```

Only after this should optional sensors or PPO profile comparisons be admitted.

## 09:41 MHTML Additions

The later exported discussion sharpened the input contract further.

The minimum driver-like self-identification profile should start from the
closed-loop body-feedback chain, not from tire diagnostics:

```text
commands:
  steer_cmd
  brake_cmd
  drive_cmd

actual actuator states:
  actual_steering_angle
  actual_brake_actuator_state
  actual_drive_actuator_state

continuous inertial feedback:
  ax
  ay
  yaw_rate

scene:
  road boundary / drivable corridor
  obstacle position
  obstacle size
```

The key claim is:

```text
passenger-like sensing can detect current sliding;
driver-like sensing must predict response to intended actions.
```

Therefore the decisive evidence is not aggregate RL success alone. A credible
self-identification claim needs:

```text
future-envelope probe accuracy
history-length improvement
wrong-history degradation
reset / zero-IMU / delayed-history degradation
noise and delay robustness
closed-loop clearance margin retention
```

The recommended profile ladder is now:

```text
H0: passenger-like inertial history
    ax, ay, yaw_rate, scene geometry

H1: driver minimal body-feedback history
    commands, actuator actuals, ax, ay, yaw_rate, scene geometry

H2: H1 + steering torque / EPS current
    tests front-grip and steering-feel information

H3: H2 + raw wheel speeds
    tests deployable vehicle proprioception beyond human body feel

H4: H2 + roll / pitch / vertical acceleration
    tests richer body / load-transfer feel
```

Wheel speed changed status in the discussion:

```text
not required for a human-like minimum claim;
still a strong optional vehicle sensor to test;
must not be converted into slip ratio before actor input.
```

`R * omega_i` and local `v_parallel_i` can be useful in a machine sensor
profile, but they should not become the human-like minimum. If a low-level
fusion profile is tested, the clean rule is:

```text
allowed optional raw/fused components:
  R * omega_i
  v_parallel_i
  optionally v_perp_i

excluded from actor:
  slip_ratio
  slip_angle
  tire saturation label
  ABS/TCS/ESC flags
  mu
  tire force
  normal load
  oracle feasibility
  reference trajectory
```

If `v_parallel_i` or `v_perp_i` are admitted later, the result must say that the
policy uses a deployable low-level fusion layer rather than a purely
human-like body-feedback input. The stronger human-like result remains H1/H2
passing the envelope probes and wrong-history gates without wheel or local
tire-speed inputs.
