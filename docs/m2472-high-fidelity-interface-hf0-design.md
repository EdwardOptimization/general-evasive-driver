# M2472 High-Fidelity Interface HF0 Design

- status: completed
- decision: `hf0_contract_route_to_implementation_preflight`
- manifest: `experiments/manifests/m2472-high-fidelity-interface-hf0-design.json`
- parent synthesis: `docs/m2471-current-sim-readiness-route-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- next milestone: `m2473-high-fidelity-interface-hf0-contract-implementation-preflight`
- high-fidelity simulation executed in M2472: `false`
- current-sim reset/rollout/policy action in M2472: `false`
- training/replay/PPO in M2472: `false`
- controller ranking/winner selection in M2472: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Problem

M2471 pivoted away from another static current-sim materialization chain and
selected high-fidelity interface preparation. HF0 must define a narrow
interface before any external simulator, Chrono backend, four-wheel backend, or
validation run is allowed.

The interface has to preserve the existing deployable control contract:

```text
actor observation:
  P0 human-view / no-oracle frame, canonical 72 values for history_length=1

actor action:
  normalized [steer_command, throttle_command, brake_command]
```

HF0 is not a platform selection or validation milestone. It is a boundary
design that makes later implementation testable.

## Current Surface Audit

Current simulator:

```text
module: src/autodrift/env.py
class: AutoDriftEnv
api:
  reset(seed, options) -> (observation, info)
  step(action) -> (observation, reward, terminated, truncated, info)
```

Current dynamics:

```text
primary model:
  src/autodrift/dynamics.py
  SingleTrackDriftModel
  VehicleState: x, y, psi, vx, vy, yaw_rate, steer, drive_force

source-only four-wheel model:
  src/autodrift/four_wheel_dynamics.py
  FourWheelDriftModel
  FourWheelState: x, y, psi, vx, vy, yaw_rate, steer, drive_force, brake_force
```

The four-wheel model is useful source infrastructure, but it is not currently a
Gym environment and is explicitly not the final high-fidelity vehicle engine.

Current vector wrappers:

```text
module: src/autodrift/vector_env.py
classes:
  SyncAutoDriftVectorEnv
  ParallelAutoDriftVectorEnv

contract:
  single_action_space.shape == (3,)
  observations are batched from env.observation_space
  done envs are reset and reset_info is attached to info
```

Current canonical observation contract:

```text
doc: docs/observation-contract.md
canonical frame size: 72
history_length: 1
action_history_mode: full
wheel_observation_mode: none
road_lookahead_count: 8
obstacle_slots: 4
include_privileged_params: false
```

P0 frame layout:

```text
0-8:
  ego velocity, body acceleration, yaw rate, steering actuator angle/rate,
  throttle actuator state, brake actuator state

9-11:
  previous physical command response fields:
  previous steer command, previous physical throttle, previous physical brake

12-43:
  eight left and eight right road-boundary points in ego frame

44-71:
  four obstacle slots:
  [present, x, y, vx, vy, half_width, half_length]
```

Actor-forbidden values already present in `info` but not in observation:

```text
mu
mass and mass_scale
cg_shift
tire stiffness scale
drive and brake scale
actuator tau scale
speed_ref
beta_target
lateral_error
heading_error
curvature
friction_step_at
obstacle_label
obstacle_required_lateral_offset
obstacle_threshold_score
required clearance or feasibility labels
reward terms and success labels
```

HF0 must keep this split. High-fidelity internals may be logged in diagnostics,
but cannot enter actor observation.

## Design Decision

Introduce a narrow internal backend boundary:

```text
DynamicsBackend
  reset(request) -> BackendResetResult
  step(action) -> BackendStepResult
  close()

P0ObservationExtractor
  actor_view -> 72-value observation
```

The backend boundary is internal infrastructure, not a public extension API. It
exists to support two concrete near-term implementations:

```text
1. current-sim adapter smoke:
   prove the boundary can wrap AutoDriftEnv without changing observation or
   action semantics.

2. later high-fidelity adapter:
   map Chrono/other high-fidelity state into the same actor-visible view.
```

Do not expose a plugin framework or simulator marketplace in HF0. The immediate
need is a fixed contract and a parity preflight.

## Backend Reset Contract

M2473 should implement typed data structures equivalent to:

```text
BackendResetRequest:
  seed: int | None
  env_config_snapshot: dict
  scenario_spec_id: str
  role_family: str
  options: dict
```

Allowed in reset request:

```text
seed
task role metadata
scenario geometry config
randomization config as simulator metadata
initial pose request
backend-specific non-actor options
```

Forbidden in actor observation:

```text
same role metadata
same randomization config
hidden physics values
oracle feasibility labels
```

Reset result:

```text
BackendResetResult:
  actor_view
  diagnostics
  backend_info
```

`actor_view` is the only object eligible for P0 observation extraction.
`diagnostics` and `backend_info` are for artifacts, audits, and baselines only.

## Backend Step Contract

M2473 should implement typed data structures equivalent to:

```text
BackendStepResult:
  actor_view
  diagnostics
  terminated_by_backend: bool
  truncated_by_backend: bool
  backend_status: str
```

`step(action)` takes exactly the deployed actor action:

```text
action.shape == (3,)
action dtype convertible to float32/float64
action values clipped to [-1, 1]
```

Action mapping remains:

```text
steer_command_physical_target = clip(action[0], -1, 1)
physical_throttle = 0.5 * (clip(action[1], -1, 1) + 1)
physical_brake = 0.5 * (clip(action[2], -1, 1) + 1)
```

The backend may map those normalized values to platform-specific actuator
targets, but it must also report actuator feedback in actor-visible physical
state:

```text
steering actuator angle
steering actuator rate
physical throttle state in [0, 1]
physical brake state in [0, 1]
previous command fields as P0 expects
```

HF0 explicitly does not change PPO action bounds. Asymmetric action bounds are
a separate trainer-interface cleanup.

## Actor-Visible State View

M2473 should define an actor-visible view with only deployable fields:

```text
ActorView:
  dt
  step_index
  ego:
    x, y, psi
    vx_body, vy_body, yaw_rate
    ax_body, ay_body
  actuators:
    steer_angle
    steer_rate
    throttle_state
    brake_state
    previous_steer_command
    previous_throttle_command
    previous_brake_command
  road:
    left_boundary_points_body[8, 2]
    right_boundary_points_body[8, 2]
  obstacles:
    slots[4] with present, x_body, y_body, vx_body, vy_body, half_width,
    half_length
```

Allowed optional future deployable fields:

```text
wheel speeds
brake pressure
steering torque
camera/lidar/radar encodings
```

Those are not part of M2472/M2473 and must require separate admission gates
before entering actor input.

## Diagnostics Boundary

Backend diagnostics may include:

```text
raw high-fidelity vehicle state
hidden physics values
per-wheel force, slip, load, or tire-state values
contact events
collision details
simulator status
solver convergence status
wall-clock runtime
backend-specific warning/error codes
```

Diagnostics must not be consumed by deployable `ActorPolicy`.

Any M2473 implementation must include a machine-checkable claim-boundary row
or summary fields:

```text
actor_input_contract_changed: false
action_contract_changed: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
```

## P0 Observation Extractor

M2473 should implement a deterministic extractor:

```text
P0ObservationExtractor.extract(actor_view) -> np.ndarray shape (72,)
```

Extractor requirements:

```text
1. preserve docs/observation-contract.md field order;
2. normalize fields using the current P0 scales;
3. emit four obstacle slots even when fewer obstacles are present;
4. emit eight left and eight right road boundary points;
5. never read diagnostics or backend_info;
6. reject actor_view payloads that cannot produce a 72-value frame;
7. expose a static field map for tests and review artifacts.
```

The current-sim adapter may delegate to `AutoDriftEnv` observation for parity,
but it must still check that the result is a canonical 72-value P0 frame under:

```text
history_length == 1
action_history_mode == "full"
wheel_observation_mode == "none"
include_privileged_params == false
road_lookahead_count == 8
obstacle_slots == 4
```

## Scenario Taxonomy Mapping

HF0 maps current-sim role labels to backend-neutral task roles:

```text
R0_stable_avoidable:
  stable avoidable / AEB feasible

R1_aeb_infeasible_stable_aes:
  stable AES / AEB infeasible

R2_drift_required_recovery:
  drift-required recovery / combined-slip maneuver

R3_hidden_dynamics_robustness:
  hidden dynamics and actuator variation

R4_unavoidable_mitigation:
  unavoidable collision mitigation
```

These labels remain scenario metadata. They must not enter actor observation.

## Failure And Status Taxonomy

M2473 should implement status strings at least for:

```text
reset_success
reset_failed_backend_error
reset_failed_nonfinite_state
reset_failed_actor_contract
step_success
step_failed_backend_error
step_failed_nonfinite_state
step_failed_actor_contract
backend_unsupported_feature
diagnostics_leak_blocked
```

Task-level outcomes remain separate from backend status:

```text
collision
hard_offtrack_failure
soft_offtrack_violation
obstacle_pass
max_steps
speed_too_low
speed_too_high
yaw_rate_limit
non_finite_state
```

This separation prevents a simulator failure from being reported as a driver
failure.

## M2473 Implementation Preflight

Recommended next milestone:

```text
m2473-high-fidelity-interface-hf0-contract-implementation-preflight
```

M2473 should implement only local, no-external-sim infrastructure:

```text
src/autodrift/high_fidelity_interface.py
tests/test_high_fidelity_interface.py
src/autodrift/high_fidelity_interface_preflight.py
runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json
docs/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.md
```

M2473 focused checks:

```text
canonical current-sim P0 reset observation shape == 72
canonical current-sim P0 step observation shape == 72
single_action_space.shape == (3,)
invalid action shape is rejected
diagnostic hidden values are not read by P0ObservationExtractor
actor/action contract changed flags are false
no external simulator is imported or required
```

M2473 must not:

```text
run high-fidelity simulation
run measured validation
train
rank controller families
select a winner
claim high-fidelity validation readiness
claim paper/self-ID/FW-vs-GRU evidence
```

## Claims

Allowed after M2472:

```text
HF0 interface boundary is designed.
M2473 implementation/preflight is admissible.
The actor and action contracts remain unchanged at design level.
```

Not allowed after M2472:

```text
high-fidelity validation readiness
high-fidelity simulation result
current-sim benchmark readiness
controller-family comparison readiness
driver performance improvement
finite-window-vs-GRU conclusion
level3 self-ID claim
```

## Decision

Decision:

```text
hf0_contract_route_to_implementation_preflight
```

Next:

```text
m2473-high-fidelity-interface-hf0-contract-implementation-preflight
```

M2473 should turn this design into checked code and a preflight artifact before
any high-fidelity backend or validation run is attempted.
