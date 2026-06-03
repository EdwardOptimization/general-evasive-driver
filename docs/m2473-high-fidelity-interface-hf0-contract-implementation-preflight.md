# M2473 High-Fidelity Interface HF0 Contract Implementation Preflight

- status: completed
- result_class: `hf0_contract_preflight_pass`
- manifest: `experiments/manifests/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.json`
- parent design: `docs/m2472-high-fidelity-interface-hf0-design.md`
- route plan: `docs/post-m2470-route-plan.md`
- implementation: `src/autodrift/high_fidelity_interface.py`
- preflight CLI: `src/autodrift/high_fidelity_interface_preflight.py`
- focused tests: `tests/test_high_fidelity_interface.py`
- summary: `runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json`
- next milestone: `m2474-high-fidelity-interface-current-sim-adapter-smoke`
- high-fidelity simulation executed in M2473: `false`
- external high-fidelity dependency imported in M2473: `false`
- policy rollout/training/replay/PPO/ranking/winner selection in M2473: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2473 turns the M2472 HF0 interface design into checked local code before any
external high-fidelity backend, Chrono adapter, measured validation, training,
or controller-family ranking is allowed.

The implementation keeps the deployed actor contract fixed:

```text
actor observation:
  canonical P0 human-view/no-oracle frame
  shape: 72

actor action:
  normalized [steer_command, throttle_command, brake_command]
  shape: 3
```

## Implemented Boundary

`src/autodrift/high_fidelity_interface.py` now defines:

```text
BackendResetRequest
BackendResetResult
BackendStepResult
DynamicsBackend
ActorView
EgoView
ActuatorView
RoadView
ObstacleSlotView
P0ObservationExtractor
```

`ActorView` is the only object eligible for P0 observation extraction.
Diagnostics and backend info remain separate audit/artifact channels and are
not consumed by the extractor.

The action validator accepts exactly shape `(3,)`, requires finite values, and
clips the deployed normalized action to `[-1, 1]`. The physical command mapping
remains:

```text
steer = clip(action[0], -1, 1)
physical_throttle = 0.5 * (clip(action[1], -1, 1) + 1)
physical_brake = 0.5 * (clip(action[2], -1, 1) + 1)
```

## Preflight Result

The required preflight summary reports:

```text
result_class: hf0_contract_preflight_pass
status_pass: true
observation_shape: 72
step_observation_shape: 72
action_shape: 3
p0_extractor_shape: 72
canonical_p0_config: true
invalid_action_shape_rejected: true
actor_input_contract_changed: false
action_contract_changed: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
external_high_fidelity_required: false
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
```

The preflight observed `29` diagnostic-only keys in current-sim `info`, while
the P0 extractor consumed only `ActorView`. Those hidden/oracle/diagnostic
values remain artifact-side diagnostics and do not enter actor input.

The zero normalized action maps to:

```text
[steer, physical_throttle, physical_brake] = [0.0, 0.5, 0.5]
```

That confirms current PPO action bounds and deployed pedal mapping are
unchanged in HF0.

## Evidence Scope

M2473 is interface infrastructure only. It proves that the local HF0 contract
can preserve the canonical current-sim P0 observation/action contract and
separate diagnostics from actor-visible state.

M2473 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification. It runs one bounded current-sim reset and one bounded
current-sim step only as shape/parity preflight, not as measured rollout or
policy evaluation.

## Commands

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_high_fidelity_interface.py
```

Result:

```text
5 passed
```

```text
PYTHONPATH=src python -m autodrift.high_fidelity_interface_preflight --output-dir runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight --next-blocker m2474-high-fidelity-interface-current-sim-adapter-smoke
```

Result:

```text
result_class=hf0_contract_preflight_pass
status_pass=True
```

## Next

Route to `m2474-high-fidelity-interface-current-sim-adapter-smoke`.

M2474 should implement or exercise a current-sim adapter through the HF0
boundary over a small bounded seed set. It must keep observation shape `72`,
action shape `3`, and diagnostics separation intact. It must not run external
high-fidelity simulation, training, ranking, winner selection, or any
validation/paper verdict claim.
