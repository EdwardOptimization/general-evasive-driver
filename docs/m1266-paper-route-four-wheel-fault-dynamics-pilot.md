# M1266 Paper-Route Four-Wheel Fault Dynamics Pilot

## Summary

M1266 implements the source-only four-wheel fault dynamics pilot admitted by
M1265.

Decision:

```text
four_wheel_fault_dynamics_pilot_infrastructure_pass_route_to_source_integration_design
```

Added:

```text
src/autodrift/four_wheel_dynamics.py
tests/test_four_wheel_dynamics.py
```

This is not a Gym environment replacement, not a training model, and not a
high-fidelity simulator claim. It is a bounded source primitive that exposes the
left-right force channel missing from `SingleTrackDriftModel`.

## Implemented Model

The pilot defines:

```text
FourWheelVehicleParams
FourWheelFaultScales
FourWheelState
WheelForce
FourWheelForces
FourWheelDriftModel
```

The control contract remains:

```text
steer
throttle
brake
```

No per-wheel controls are exposed to the actor.

The model computes contact-patch forces for:

```text
front_left
front_right
rear_left
rear_right
```

and yaw moment from wheel positions:

```text
Mz = sum(x_i * Fy_i - y_i * Fx_i)
```

Supported source-only fault scale helpers:

```text
split_mu(left_scale, right_scale)
single_wheel_grip_collapse(wheel, mu_scale, lateral_stiffness_scale)
single_wheel_brake_pull(wheel, brake_scale)
halfshaft_torque_loss(wheel, drive_scale)
```

Fault labels and per-wheel scales are simulator/source metadata only. They are
not actor inputs.

## Focused Evidence

Validation command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_dynamics.py
```

Result:

```text
5 passed in 0.06s
```

Compile command:

```bash
python -m compileall -q src tests
```

Result:

```text
passed
```

Measured asymmetric responses:

```text
left_low split-mu yaw_moment:  -786.3186173
right_low split-mu yaw_moment:  786.3186173

front_left brake pull yaw_moment:   750.1433310
front_right brake pull yaw_moment: -750.1433310

rear_left nominal capacity:   3086.2084821
rear_left collapsed capacity:  617.2416964
rear_left nominal Fy:         -686.2726480
rear_left collapsed Fy:       -160.3235442
```

These are the missing source-level signals:

```text
left-right split-mu produces signed yaw response under braking
single-wheel brake pull produces signed yaw response
single-wheel grip collapse reduces available force capacity
```

## Important Test Adjustment

The initial split-mu test used a fresh brake command from zero brake pressure.
With actuator lag, the first step did not build enough brake force to saturate
the low-mu side, so yaw moment was zero. The test was corrected to evaluate a
source state where brake pressure is already established.

Interpretation:

```text
The model should express split-mu yaw when the tire/brake state reaches the
asymmetric capability boundary. The first actuator-lag step is not that state.
```

This is a useful integration lesson for later source mining: source collectors
must include actuator/response timing, not only instantaneous fault labels.

## Fidelity Limits

M1266 remains a compact model:

```text
quasi-static front/rear normal load split
no full suspension kinematics
no thermal tire state
no combined transient relaxation length
no ABS controller
no road mesh contact
no true tire carcass / puncture physics
```

Allowed claim:

```text
The in-repo source model can express finite signed left-right asymmetric fault
responses that the single-track source model cannot express.
```

Blocked claims:

```text
high-fidelity vehicle dynamics
real tire blowout physics
real split-mu validation
real stuck-caliper validation
source-positive capability-separable rows
actor self-identification evidence
paper-level result
```

## Guardrails

M1266 did not:

```text
train controllers
run PPO
promote checkpoints
use private holdout
change actor inputs
lower accepted-source thresholds
replace the main Gym env
claim source-positive rows from unit tests
```

## Next Step

The model primitive is ready for an integration design, not direct training.

Next:

```text
m1267-paper-route-four-wheel-fault-source-integration-design
```

That design should define how to:

```text
collect four-wheel source snapshots,
map them to existing human-view observations,
keep per-wheel/fault metadata out of actor inputs,
adapt capability-separable source evaluation,
and compare source shape against M1259/M1262 without changing thresholds.
```
