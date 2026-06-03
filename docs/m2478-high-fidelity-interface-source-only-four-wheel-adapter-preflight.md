# M2478 High-Fidelity Interface Source-Only Four-Wheel Adapter Preflight

- status: completed
- result_class: `source_only_four_wheel_adapter_preflight_pass`
- manifest: `experiments/manifests/m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight.json`
- parent synthesis: `docs/m2477-high-fidelity-interface-preparation-branch-synthesis.md`
- implementation: `src/autodrift/four_wheel_hf0_adapter.py`
- focused tests: `tests/test_four_wheel_hf0_adapter.py`
- summary: `runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json`
- next milestone: `m2479-high-fidelity-interface-scenario-taxonomy-mapping-design`
- external high-fidelity simulation installed/imported/executed in M2478: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2478: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2478 adds executable adapter evidence after M2477 synthesis. It wraps the
repository-local `FourWheelDriftModel` behind an HF0-style backend without
external high-fidelity dependencies.

This is source-only adapter preflight. It is not high-fidelity validation.

## Implemented Boundary

`src/autodrift/four_wheel_hf0_adapter.py` adds:

```text
FourWheelHF0Backend
run_source_only_four_wheel_adapter_preflight
CLI: python -m autodrift.four_wheel_hf0_adapter
```

The adapter maps:

```text
FourWheelState
  -> ActorView
  -> P0ObservationExtractor
  -> 72-value P0 observation
```

The deployed action shape remains `3`. The same HF0 action validator and
physical command mapping are used.

Four-wheel hidden/internal values remain diagnostics only:

```text
wheel forces
wheel slip/load-like values
fault scales
model params
source-only model state
```

Those values do not enter `ActorView` and are not read by
`P0ObservationExtractor`.

## Preflight Result

The required summary reports:

```text
result_class: source_only_four_wheel_adapter_preflight_pass
status_pass: true
backend_id: source_only_four_wheel_hf0
source_only_model: FourWheelDriftModel
reset_count: 1
step_count: 2
observation_shape: 72
step_observation_shapes: [72, 72]
action_shape: 3
p0_extractor_shape: 72
diagnostic_wheel_force_counts: [4, 4]
four_wheel_hidden_diagnostics_present: true
fault_scales_diagnostic_only: true
wheel_forces_diagnostic_only: true
actor_input_contract_changed: false
action_contract_changed: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
external_high_fidelity_required: false
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
```

Both bounded steps returned backend status `running`.

## Evidence Scope

M2478 proves only that a repository-local four-contact-patch source model can
be wrapped through the HF0 actor/action boundary with four-wheel diagnostics
kept out of actor input.

M2478 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.

## Commands

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_hf0_adapter.py
```

Result:

```text
3 passed
```

```text
PYTHONPATH=src python -m autodrift.four_wheel_hf0_adapter --output-dir runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight --next-blocker m2479-high-fidelity-interface-scenario-taxonomy-mapping-design
```

Result:

```text
result_class=source_only_four_wheel_adapter_preflight_pass
status_pass=True
observation_shape=72
step_count=2
```

## Next

Route to `m2479-high-fidelity-interface-scenario-taxonomy-mapping-design`.

M2479 should map the HF0 scenario taxonomy across current-sim and source-only
four-wheel adapter surfaces before any further external-backend or validation
step. It must not run external simulation, training, ranking, winner selection,
or validation/paper verdict claims.
