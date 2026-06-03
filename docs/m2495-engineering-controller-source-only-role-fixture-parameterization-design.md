# M2495 Engineering Controller Source-Only Role Fixture Parameterization Design

- status: completed
- decision: `source_only_role_fixture_parameterization_design_route_to_implementation_preflight`
- manifest: `experiments/manifests/m2495-engineering-controller-source-only-role-fixture-parameterization-design.json`
- parent audit: `docs/m2494-engineering-controller-source-only-role-metric-panel-result-audit.md`
- next milestone: `m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight`
- external high-fidelity simulation installed/imported/executed in M2495: `false`
- policy action/measured validation/training/replay/PPO/ranking/winner selection in M2495: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Problem

M2494 accepted the M2493 telemetry infrastructure but found that all three role
metric panel rows were numerically identical. The source-only role fixtures are
currently distinct as metadata, but `FourWheelHF0Backend.reset` does not vary
the dynamics by `fixture_id` or `role_family`.

M2495 designs the repair boundary before implementation:

```text
turn admitted source-only role fixture metadata into explicit reset-time
dynamics parameterization without changing actor inputs or action contract.
```

This is still source-only engineering infrastructure. It is not validation,
driver performance, or paper evidence.

## Contract

Introduce a source-only fixture dynamics contract, conceptually:

```python
@dataclass(frozen=True)
class SourceOnlyRoleFixtureDynamicsSpec:
    fixture_id: str
    role_family: str
    initial_state: FourWheelState
    fault_scales: FourWheelFaultScales
    road: RoadView
    obstacles: tuple[ObstacleSlotView, ...]
    diagnostic_tags: Mapping[str, str | float | int | bool]
```

Allowed role-specific variation:

```text
initial_state:
  x
  y
  psi
  vx
  vy
  yaw_rate
  steer
  drive_force
  brake_force

fault_scales:
  mu
  lateral_stiffness
  brake
  drive
  longitudinal_drag

road:
  left_boundary_points_body
  right_boundary_points_body

obstacles:
  present
  x_body
  y_body
  vx_body
  vy_body
  half_width
  half_length

diagnostic_tags:
  fixture_source
  role_family
  parameterization_version
  differentiation_reason
```

Forbidden actor-input variation:

```text
role labels as actor features
fixture labels as actor features
feasibility classes
hidden/fault scales as actor features
wheel forces as actor features
oracle labels
TTC
required clearance
reward terms
success/progress labels
```

The actor may observe the physical consequences of a scenario through the
existing P0 actor view: ego state, actuator state, road geometry, and obstacle
slots. That is not a leak. The labels and hidden diagnostic values remain out of
the actor-visible 72-vector.

## Backend API Design

M2496 should keep the existing `FourWheelHF0Backend` usable without fixtures,
then add an opt-in source-only fixture spec path:

```text
FourWheelHF0Backend(fixture_spec: SourceOnlyRoleFixtureDynamicsSpec | None = None)
```

Implementation direction:

```text
1. Preserve the existing default constructor behavior for old tests.
2. If fixture_spec is present:
   - initialize state from fixture_spec.initial_state
   - initialize fault scales from fixture_spec.fault_scales
   - emit fixture_spec.road in ActorView
   - emit fixture_spec.obstacles in ActorView
   - expose fixture_spec diagnostic tags in diagnostics only
3. Keep action shape and action normalization unchanged.
4. Keep P0ObservationExtractor output shape exactly 72.
5. Do not add role or fixture labels to P0ObservationExtractor fields.
```

The current module-level `_fixture_road()` and `_fixture_obstacles()` should
become backend-instance helpers so the default path and fixture-spec path share
the same actor-view construction boundary.

## Initial Fixture Specs

M2496 should implement three conservative source-only fixture specs. These are
not meant to define success. They only need to make role fixtures dynamically
different enough for engineering telemetry to be meaningful.

```text
stable_aes:
  fixture_id: hf0_four_wheel_stable_aes_fixture
  initial_state:
    x: 0.0
    y: 0.0
    psi: 0.0
    vx: 9.0
    vy: 0.05
    yaw_rate: 0.02
    steer: 0.0
  fault_scales:
    nominal
  obstacle:
    present: 1.0
    x_body: 32.0
    y_body: -0.5
    vx_body: -8.0
    vy_body: 0.0
    half_width: 0.75
    half_length: 0.75
  differentiation_reason: higher speed nominal-grip avoidable source-only AES reference

drift_required_recovery:
  fixture_id: hf0_four_wheel_drift_required_recovery_fixture
  initial_state:
    x: 0.0
    y: 0.45
    psi: 0.04
    vx: 10.0
    vy: 0.55
    yaw_rate: 0.18
    steer: 0.02
  fault_scales:
    split_mu(left_scale=0.72, right_scale=0.95)
  obstacle:
    present: 1.0
    x_body: 26.0
    y_body: 0.75
    vx_body: -7.0
    vy_body: -0.2
    half_width: 0.8
    half_length: 0.9
  differentiation_reason: lateral velocity yaw and asymmetric grip create recovery-oriented source-only dynamics

unavoidable_mitigation:
  fixture_id: hf0_four_wheel_unavoidable_mitigation_fixture
  initial_state:
    x: 0.0
    y: -0.35
    psi: -0.03
    vx: 8.2
    vy: -0.35
    yaw_rate: -0.14
    steer: -0.01
  fault_scales:
    uniform_grip(mu_scale=0.68, lateral_stiffness_scale=0.72)
  obstacle:
    present: 1.0
    x_body: 17.0
    y_body: 0.15
    vx_body: -6.5
    vy_body: 0.1
    half_width: 0.95
    half_length: 1.0
  differentiation_reason: low grip close obstacle mitigation-oriented source-only dynamics
```

All remaining obstacle slots should be zero-filled. Roads should preserve the
same shape as the existing P0 road view while allowing small lateral offsets or
curvature-like point changes by role.

## M2496 Preflight

M2496 should be reset-only. It should not execute policy actions.

Required artifacts:

```text
runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json
runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/fixture_parameterization_rows.csv
runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/reset_differentiation_rows.csv
```

Required checks:

```text
spec_count: 3
roles: stable_aes drift_required_recovery unavoidable_mitigation
reset_count: 3
policy_action: false
policy_rollout_run: false
all_reset_observations_shape_72: true
action_shape: 3
actor_input_contract_changed: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
success_labels_enter_actor_input: false
ttc_enter_actor_input: false
required_clearance_enter_actor_input: false
role_labels_enter_actor_input: false
fixture_labels_enter_actor_input: false
```

Differentiation gates:

```text
unique_initial_state_digest_count: 3
unique_fault_scale_digest_count: at least 2
unique_obstacle_digest_count: 3
pairwise_reset_observation_l2_min: > 1e-3
pairwise_state_digest_unique: true
role_metadata_only: true
```

The reset observation may differ because actor-visible physical conditions
differ. The hidden labels and diagnostic-only fields must not appear as actor
features.

## Implementation Tests

M2496 should add focused tests:

```text
tests/test_hf0_source_only_role_fixture_parameterization.py
```

Minimum test coverage:

```text
build_source_only_role_fixture_specs returns exactly three specs.
Each spec uses an admitted source-only fixture id and expected role family.
Each backend reset emits a 72-dimensional P0 observation.
Pairwise reset observations are not identical.
Fault scales and initial state diagnostics are present only in diagnostics.
Role labels and fixture labels do not enter actor input.
No policy action is executed by the preflight.
```

Existing tests for the default backend should continue to pass. The default
`FourWheelHF0Backend()` path must remain nominal.

## Claim Boundary

M2495/M2496 can support:

```text
source-only role fixture parameterization exists
role reset observations are dynamically differentiated
actor/action contract is preserved
diagnostics remain outside actor input
```

They cannot support:

```text
driver performance
success rate
role-specific recovery quality
controller ranking
winner selection
checkpoint promotion
high-fidelity validation
current-sim verdict
paper evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

## Route Decision

M2495 routes to:

```text
m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight
```

M2496 should implement the reset-only source-only fixture parameterization
preflight. It must not run policy actions or compute success-rate/verdict
metrics. If it passes, a later audit can decide whether to rerun the
nonverdict role metric panel on dynamically differentiated source-only fixtures.
