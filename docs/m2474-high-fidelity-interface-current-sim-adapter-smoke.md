# M2474 High-Fidelity Interface Current-Sim Adapter Smoke

- status: completed
- result_class: `current_sim_adapter_smoke_pass`
- manifest: `experiments/manifests/m2474-high-fidelity-interface-current-sim-adapter-smoke.json`
- parent preflight: `docs/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.md`
- implementation: `src/autodrift/high_fidelity_interface.py`
- smoke CLI: `src/autodrift/high_fidelity_interface_adapter_smoke.py`
- focused tests: `tests/test_high_fidelity_interface.py`
- summary: `runs/m2474_high_fidelity_interface_current_sim_adapter_smoke/summary.json`
- next milestone: `m2475-high-fidelity-interface-external-backend-route-design`
- external high-fidelity simulation/import executed in M2474: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2474: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2474 exercises the checked HF0 boundary through the current simulator before
any external high-fidelity adapter work. This is a bounded contract smoke, not a
controller benchmark or validation run.

The adapter path is:

```text
AutoDriftEnv.reset/step
  -> canonical P0 observation
  -> ActorView reconstruction
  -> P0ObservationExtractor
  -> 72-value actor observation parity check
```

Current-sim `info` remains diagnostics only. It is carried in
`BackendResetResult.diagnostics` or `BackendStepResult.diagnostics`, not in
`ActorView` and not in the P0 extractor input.

## Implemented Adapter

`src/autodrift/high_fidelity_interface.py` now includes:

```text
actor_view_from_p0_observation
CurrentSimDynamicsBackend
run_current_sim_adapter_smoke
```

`src/autodrift/high_fidelity_interface_adapter_smoke.py` writes the M2474
summary artifact.

The current-sim adapter requires the canonical P0 config:

```text
history_length: 1
action_history_mode: full
wheel_observation_mode: none
road_lookahead_count: 8
obstacle_slots: 4
include_privileged_params: false
```

## Smoke Result

The required summary reports:

```text
result_class: current_sim_adapter_smoke_pass
status_pass: true
backend_id: current_sim_autodrift_hf0
seed_count: 3
seeds: [2474, 2475, 2476]
actions_per_seed: 2
current_sim_reset_count: 3
current_sim_step_count: 6
observation_shape: 72
action_shape: 3
p0_extractor_shape: 72
canonical_p0_config: true
max_extractor_parity_abs_error: 5.960464477539063e-08
actor_input_contract_changed: false
action_contract_changed: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
external_high_fidelity_required: false
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
measured_validation_run: false
```

All three reset observations and all six bounded step observations preserve
shape `72`. The maximum extractor parity error is within float32 roundoff.

The smoke saw `29` diagnostic-only current-sim keys, including hidden dynamics
and oracle-style labels, but those keys stayed in diagnostics and were not read
by actor observation extraction.

## Evidence Scope

M2474 establishes that the HF0 backend boundary can wrap the current simulator
while preserving the actor/action contract and diagnostics separation.

M2474 does not establish high-fidelity validation readiness, current-sim
benchmark readiness, driver performance, finite-window-vs-GRU evidence, or
level-3 self-identification. The reset/step counts are bounded adapter smoke
counts only.

## Commands

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_high_fidelity_interface.py
```

Result:

```text
8 passed
```

```text
PYTHONPATH=src python -m autodrift.high_fidelity_interface_adapter_smoke --output-dir runs/m2474_high_fidelity_interface_current_sim_adapter_smoke --next-blocker m2475-high-fidelity-interface-external-backend-route-design
```

Result:

```text
result_class=current_sim_adapter_smoke_pass
status_pass=True
reset_count=3
step_count=6
```

## Next

Route to `m2475-high-fidelity-interface-external-backend-route-design`.

M2475 should select the next bounded external-backend route and admission
criteria without importing, installing, or running an external high-fidelity
simulator. The design must keep HF0 actor/action contracts fixed and route to a
small implementation/preflight step rather than a validation verdict.
