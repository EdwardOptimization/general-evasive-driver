# M2551 Engineering Controller Route A Baseline HF1 P0 Parity Smoke Design

- status: completed
- decision: `route_to_hf1_p0_parity_smoke_materialization_preflight`
- manifest: `experiments/manifests/m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design.json`
- parent synthesis: `docs/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.md`
- source interface contract: `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md`
- source parity artifact: `runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv`
- follow-up manifest: `experiments/manifests/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.json`
- next: `m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight`

## Scope

M2551 designs the HF1 P0 parity smoke materialization required by
`docs/post-m2470-route-plan.md`. It converts the accepted HF0 contract and
runtime artifacts into an evidence-producing M2552 specification.

M2551 is design-only. It does not install, import, or run an external
high-fidelity simulator. It does not execute policy actions, train, replay,
rank controllers, promote checkpoints, compute success rates, or claim
validation or driver performance.

## Route-Plan Binding

The post-M2470 route defines HF1 as:

```text
P0 observation extractor
[steer, throttle, brake] action mapping
observation shape and value-range parity checks
no hidden/oracle actor inputs
```

M2552 should therefore materialize row-level checks for the P0 actor-visible
contract, not a high-fidelity validation result. External-backend work remains
limited to adapter-boundary checks until a later route explicitly permits
installation/import/runtime.

## Source Contracts

M2552 should bind to the current repo contract:

```text
P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
ROAD_LOOKAHEAD_COUNT = 8
OBSTACLE_SLOT_COUNT = 4
DIAGNOSTIC_ONLY_KEYS = 33
```

P0 observation layout:

```text
ego dynamics: 5 values
actuator state and previous commands: 7 values
left road boundary: 8 points * 2 values
right road boundary: 8 points * 2 values
obstacle slots: 4 slots * 7 values
total: 72 values
```

Action contract:

```text
actor action: [steer, throttle, brake]
normalized range: [-1.0, 1.0]
physical control: [steer, 0.5 * (throttle + 1), 0.5 * (brake + 1)]
```

Actor-visible components remain limited to `ActorView`, `EgoView`,
`ActuatorView`, `RoadView`, `ObstacleSlotView`, `P0ObservationExtractor`,
`validate_actor_action`, and `physical_control_from_action`. Diagnostics-only
keys must remain outside the actor field map.

## M2552 Required Artifacts

M2552 should write:

```text
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_actor_visible_field_parity_rows.csv
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_observation_value_range_checks.csv
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_action_mapping_parity_checks.csv
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_external_backend_boundary_checks.csv
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_diagnostics_exclusion_checks.csv
runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/materialization_gate_matrix.csv
docs/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.md
```

## Actor-Visible Field Parity Rows

M2552 should include rows for:

- `ego_dynamic_block`: indices `0..4`, five normalized ego response values
- `actuator_state_block`: indices `5..8`, steering/throttle/brake state values
- `previous_command_block`: indices `9..11`, previous deployed command values
- `left_road_boundary_block`: indices `12..27`, eight body-frame points
- `right_road_boundary_block`: indices `28..43`, eight body-frame points
- `obstacle_slot_block`: indices `44..71`, four obstacle slots
- `full_p0_extract`: full 72-value extractor output

Each row should record:

```text
row_id
actor_view_component
source_path
p0_index_start
p0_index_end
expected_count
observed_count
normalization_policy
finite_required
expected_observation_shape
observed_observation_shape
hidden_or_oracle_actor_input_detected
status_pass
claim_boundary
```

Pass criteria:

- row spans cover exactly `0..71` without gaps or overlaps
- observed full P0 shape is `72`
- all values are finite
- no diagnostics-only or oracle fields enter any row
- no actor input contract is changed

## Observation Value-Range Checks

M2552 should include value-range rows for:

- ego velocity/yaw/acceleration normalization
- actuator state and previous command bounds
- road boundary body-frame normalization
- obstacle presence, pose, velocity, and size normalization
- full-vector finite and max-absolute-value smoke

Each row should record:

```text
range_check_id
component_family
source_indices
expected_shape
finite_observation
max_abs_observation_value
allowed_range_policy
range_violation_count
status_pass
claim_boundary
```

Pass criteria:

- all rows are finite
- values respect the declared normalization policy or are explicitly reported
  as source-smoke values without clipping
- no value-range row is interpreted as driver performance or validation

## Action Mapping Parity Checks

M2552 should repeat the deployed action mapping checks as HF1 gate rows:

- zero action `[0.0, 0.0, 0.0]`
- full negative action `[-1.0, -1.0, -1.0]`
- full positive action `[1.0, 1.0, 1.0]`
- clipped high action `[2.0, 2.0, 2.0]`
- clipped low action `[-2.0, -2.0, -2.0]`
- invalid shape rejection
- non-finite action rejection

Each row should record:

```text
action_check_id
input_action
expected_action_shape
validated_action
physical_control
expected_physical_control
invalid_input_rejected
finite_required
action_within_bounds
status_pass
claim_boundary
```

Pass criteria:

- valid actions retain action shape `3`
- finite out-of-range actions clip to `[-1.0, 1.0]`
- throttle and brake map to `[0.0, 1.0]`
- invalid shape and non-finite inputs are rejected
- no action row changes the deployed actor action contract

## External-Backend Boundary Checks

M2552 should not install, import, or run Chrono or any other external
high-fidelity simulator. Its external-backend rows are adapter-boundary checks
only:

- `dynamics_backend_protocol`: `backend_id`, `dt`, `reset`, `step`, `close`
- `backend_reset_request_schema`: seed, config snapshot, scenario id, role, options
- `backend_reset_result_schema`: actor view, diagnostics, backend info
- `backend_step_result_schema`: actor view, diagnostics, termination flags, backend status
- `action_input_contract`: deployed `[steer, throttle, brake]` action input
- `external_dependency_guard`: no external package import/runtime in M2552

Each row should record:

```text
boundary_check_id
required_interface
source_component
external_backend_required
external_package_imported
external_backend_run
adapter_runtime_binding_allowed
status_pass
claim_boundary
```

Pass criteria:

- required adapter boundary is defined in repo source
- external backend required/imported/run flags remain false
- the boundary does not expose hidden dynamics or oracle labels to the actor
- no row is claimed as high-fidelity validation readiness or result

## Diagnostics Exclusion Checks

M2552 should materialize one diagnostics-exclusion table covering the 33
`DIAGNOSTIC_ONLY_KEYS` entries. Each row should record:

```text
diagnostic_key
source_component
actor_visible_allowed
present_in_actor_field_map
hidden_or_oracle_risk
status_pass
claim_boundary
```

Pass criteria:

- every diagnostics-only key is checked
- no diagnostics-only key is present in the actor field map
- hidden dynamics, oracle labels, success/progress signals, TTC-like values,
  tire/slip parameters, reward terms, and termination labels remain outside
  actor input

## Gate Matrix

M2552 passes only if:

- all required artifacts exist
- actor-visible field parity rows cover the complete P0 layout
- observation shape is `72` and action shape is `3`
- observation value-range smoke rows pass
- action mapping parity rows pass
- diagnostics-only keys remain outside actor input
- external-backend boundary rows do not install, import, or run external
  high-fidelity simulation
- no policy rollout, training, replay, PPO, ranking, winner selection,
  checkpoint promotion, success-rate, validation, driver-performance, paper,
  FW-vs-GRU, current-sim, high-fidelity validation, or self-ID claim is made

## Follow-Up

Route to M2552 materialization/preflight. M2552 may add a bounded
source-only materializer and tests to write the artifacts above. It must not
run external high-fidelity simulation or interpret parity-smoke artifacts as
driver performance.
