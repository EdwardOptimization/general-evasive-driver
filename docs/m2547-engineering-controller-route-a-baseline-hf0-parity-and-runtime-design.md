# M2547 Engineering Controller Route A Baseline HF0 Parity And Runtime Design

- status: completed
- decision: `route_to_route_a_hf0_parity_and_runtime_materialization_preflight`
- manifest: `experiments/manifests/m2547-engineering-controller-route-a-baseline-hf0-parity-and-runtime-design.json`
- parent synthesis: `docs/m2546-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-result-synthesis.md`
- source interface contract: `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md`
- source boundary map: `runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_boundary_map.csv`
- follow-up manifest: `experiments/manifests/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.json`
- next: `m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight`

## Scope

M2547 designs a bounded HF0 P0 parity and runtime/inference-cost
materialization step for Route A. The design prepares M2548 to materialize
machine-readable artifacts, not to validate driver performance.

M2547 does not install, import, or run external high-fidelity simulation. It
does not execute new policy rollouts, train, replay, rank, promote, compute
success rates, or claim validation.

## Source Contracts

M2548 should bind to existing source-level interfaces:

- `P0_OBSERVATION_DIM = 72`
- `ACTION_DIM = 3`
- `P0ObservationExtractor.extract`
- `validate_actor_action`
- `physical_control_from_action`
- `CurrentSimDynamicsBackend`
- `FourWheelHF0Backend`
- `DIAGNOSTIC_ONLY_KEYS`
- Route A policy checkpoints admitted in M2544

Actor-visible fields remain limited to ego response, actuator state,
previous physical commands, road/free-space geometry, obstacle geometry, and
online recurrent/history state. Diagnostic-only hidden values and oracle
labels must stay outside actor input.

## M2548 Required Artifacts

M2548 should write:

```text
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/action_mapping_checks.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/runtime_report_schema.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/actor_inference_cost_rows.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/materialization_gate_matrix.csv
docs/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.md
```

## P0 Parity Checks

The parity materialization should include rows for:

- deterministic default `ActorView` extraction
- `CurrentSimDynamicsBackend` reset extraction
- `CurrentSimDynamicsBackend` canned-action step extraction
- `FourWheelHF0Backend` reset extraction
- `FourWheelHF0Backend` canned-action step extraction

Each row should record:

```text
check_id
backend_id
source_component
actor_visible_component_family
expected_observation_shape
observed_observation_shape
finite_observation
max_abs_observation_value
value_range_policy
diagnostic_only_keys_checked
hidden_or_oracle_actor_input_detected
parity_abs_error
status_pass
claim_boundary
```

Pass criteria:

- observed P0 observation shape is `72`
- observation values are finite
- extractor parity error is zero or within `1e-6` where a source observation exists
- diagnostics-only keys are checked but not actor-visible
- no hidden/oracle actor input is detected

## Action Mapping Checks

The action mapping materialization should include rows for:

- zero action `[0.0, 0.0, 0.0]`
- full negative action `[-1.0, -1.0, -1.0]`
- full positive action `[1.0, 1.0, 1.0]`
- clipped high action `[2.0, 2.0, 2.0]`
- clipped low action `[-2.0, -2.0, -2.0]`
- invalid shape rejection
- non-finite action rejection

Each row should record:

```text
check_id
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

- valid action outputs retain shape `3`
- finite out-of-range values are clipped to `[-1.0, 1.0]`
- physical control maps throttle/brake from normalized `[-1, 1]` to `[0, 1]`
- invalid shapes and non-finite values are rejected
- no mapping row changes the deployed actor contract

## Runtime Report Design

M2548 should measure actor-forward inference cost for the three Route A policy
checkpoints only:

- `m1154_original_policy`
- `m2532_guarded_repair_policy`
- `m2537_mitigation_preserving_policy`

Runtime rows should use seeded synthetic P0-shaped observations and the
actor-forward timed path from M2508. They must not step an environment or
interpret action outputs as control.

Default measurement design:

```text
batch_sizes: 1, 8, 32
warmup_iterations: 10
measured_iterations: 30
expected_actor_inference_cost_rows: 270
```

The runtime report schema should include:

```text
subject_id
checkpoint_path
checkpoint_admitted
checkpoint_obs_dim
checkpoint_action_dim
checkpoint_actor_encoder
checkpoint_action_sequence_horizon
batch_size
iteration_index
device
timed_path
observation_shape
action_shape
forward_time_us
per_sample_time_us
action_finite
action_within_bounds
synthetic_observation_source
action_outputs_interpreted_as_control
ranking_or_winner_field_emitted
claim_boundary
```

Pass criteria:

- all three policy checkpoints are admitted under P0 `72/3`
- every runtime row has observation shape `72` and action shape `3`
- forward time and per-sample time are positive
- actor outputs are finite and within bounds
- row count equals `3 * 3 * 30 = 270`
- no ranking or winner field is emitted

## Gate Matrix

M2548 passes only if:

- all required artifacts exist
- P0 parity checks pass
- action mapping checks pass
- runtime rows are denominator-complete
- diagnostics-only keys remain outside actor input
- P0 `72/3` actor/action contract is preserved
- no external high-fidelity simulation is installed, imported, or executed
- no policy rollout, training, replay, PPO, ranking, winner selection, checkpoint promotion, success-rate, validation, driver-performance, paper, FW-vs-GRU, current-sim, high-fidelity validation, or self-ID claim is made

## Follow-Up

Route to M2548 materialization/preflight. M2548 may implement the materializer
and tests needed to write the artifacts above. It may use bounded local
source-only/current-sim parity smoke and actor-forward timing, but it must not
run external high-fidelity validation or interpret action outputs as
performance.
