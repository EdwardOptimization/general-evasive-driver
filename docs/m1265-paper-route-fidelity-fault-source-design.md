# M1265 Paper-Route Fidelity Fault Source Design

## Summary

M1265 designs the next source-fidelity branch after M1264 closed the
single-track/current-model richer proxy-fault branch.

Decision:

```text
fidelity_fault_source_design_admit_four_wheel_fault_dynamics_pilot
```

Open branch:

```text
paper_route_fidelity_fault_source_design
```

Admit next bounded implementation:

```text
m1266-paper-route-four-wheel-fault-dynamics-pilot
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, accepted-threshold relaxation, self-identification claim,
paper-level claim, or high-fidelity result claim occurs in M1265.

## Why Current Source Fidelity Is Insufficient

The current main dynamics model is intentionally compact:

```text
SingleTrackDriftModel
state: x, y, psi, vx, vy, yaw_rate, steer, drive_force
action: steer, throttle, brake
forces: front lateral, rear lateral, rear longitudinal
hidden variation: aggregate mu, front/rear stiffness, mass, cg, brake/drive scale, actuator tau
```

This is enough for early RL and closed-loop emergency avoidance experiments, but
it cannot represent several source families the project now needs:

```text
single-wheel grip collapse / puncture
left-right split-mu
single-wheel brake pull / stuck caliper
halfshaft or drive-side torque asymmetry
per-wheel drive/brake saturation
fault-induced yaw moment from left-right force imbalance
```

The key missing piece is not only more randomization. It is left-right force
asymmetry and per-wheel capacity. In the current model, many hidden branches
still produce similar closed-loop outcomes for different actions, so the source
miner finds action divergence without enough two-sided outcome regret.

## Design Choice

Do not jump directly to a large external simulator integration.

Do not continue current single-track proxy source repair.

Start with a minimum in-repo four-wheel/fault dynamics pilot for source mining.

Rationale:

```text
It is small enough to test and review quickly.
It gives the source constructor the missing left-right force channel.
It preserves reproducibility and artifact discipline.
It can later be validated against a high-fidelity engine.
```

External simulators remain important later, but choosing one now would mix
source-fidelity design, integration risk, licensing/runtime variability, and
research gating. The next step should first prove that a four-wheel fault source
can express the missing capability differences in a controlled local model.

## Minimum Four-Wheel Fault Pilot

Implement a source-only model:

```text
src/autodrift/four_wheel_dynamics.py
tests/test_four_wheel_dynamics.py
```

It should not replace the main training environment yet.

It should provide:

```text
FourWheelVehicleParams
FourWheelFaultSpec
FourWheelState or reuse-compatible VehicleState
FourWheelForces
FourWheelDriftModel.step(state, action, dt)
```

Use the same deployable control action contract:

```text
steer
throttle
brake
```

Do not add per-wheel controls to the actor.

Internally, distribute forces across four contact patches:

```text
front_left
front_right
rear_left
rear_right
```

Compute yaw moment from wheel positions:

```text
Mz = sum(x_i * Fy_i - y_i * Fx_i)
```

The pilot can start with a compact quasi-static load model:

```text
front/rear static load split from lf/lr
optional longitudinal load transfer from ax estimate
optional lateral load transfer from ay estimate
per-wheel normal load clipped positive
per-wheel friction ellipse
```

The exact model does not need to be production-grade. It must be deterministic,
bounded, tested, and expressive enough for source mining.

## Fault Families

The pilot should support source-only fault metadata:

```text
left_right_split_mu:
  left wheels and right wheels receive different mu scales.

single_wheel_grip_collapse:
  one wheel receives a severe mu / lateral stiffness reduction.

single_wheel_brake_pull:
  one wheel receives extra brake force or reduced brake authority asymmetrically.

halfshaft_torque_loss:
  one driven rear wheel loses drive force.

rear_or_front_axle_authority_loss:
  front or rear axle tire capacity changes, but represented per wheel.
```

These faults may enter source-mining metadata and simulator internals, but not
deployable actor inputs.

## Acceptance Gates

Accepted source thresholds remain unchanged:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

The next model pilot does not claim source-positive evidence by itself. It must
first pass model-level tests:

```text
nominal symmetric model is finite and stable over a short rollout
left-right split-mu creates a signed yaw-moment difference under braking
single-wheel brake pull creates a signed yaw-moment difference
single-wheel grip collapse reduces available lateral/longitudinal force
all outputs remain finite under extreme but bounded faults
```

Only after those pass should a later milestone integrate the model into source
collection.

## Actor Input Guardrail

The actor observation contract remains human-view/no-privileged.

Allowed actor inputs remain:

```text
ego kinematics / IMU-like response
actuator state
previous physical commands
road / obstacle geometry in ego frame
recurrent hidden state from command-response history
```

Forbidden actor inputs remain:

```text
mu
per-wheel mu
fault family / fault label
slip ratio
tire force
friction margin
oracle feasibility
source-mining labels
search outputs
teacher action labels
```

Per-wheel forces and fault labels may be logged for source mining, debugging,
and offline evaluation only.

## External Simulator Boundary

External high-fidelity engines are a later validation branch, not M1266.

A future external-engine scout should compare:

```text
vehicle/fault expressivity
determinism and seed control
headless runtime
Linux/WSL compatibility
Python API quality
license constraints
cost and install friction
ability to export source-mining snapshots
```

But M1266 should not depend on that. The immediate need is a bounded local
source-fidelity pilot.

## Next Milestone

Admit:

```text
m1266-paper-route-four-wheel-fault-dynamics-pilot
```

Scope:

```text
implement source-only four-wheel fault dynamics primitives
add focused finite/yaw-moment/unit tests
document fidelity limits
do not integrate into Gym env yet
do not train
do not run PPO
do not promote
```

Expected artifacts:

```text
src/autodrift/four_wheel_dynamics.py
tests/test_four_wheel_dynamics.py
docs/m1266-paper-route-four-wheel-fault-dynamics-pilot.md
```

M1266 passes only as infrastructure if the model primitives are deterministic,
finite, and can express signed yaw-moment differences under asymmetric faults.
It does not claim that the source-positive gap is solved.
