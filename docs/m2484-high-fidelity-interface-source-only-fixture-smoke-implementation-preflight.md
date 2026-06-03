# M2484 High-Fidelity Interface Source-Only Fixture Smoke Implementation Preflight

- status: completed
- result_class: `hf0_source_only_fixture_smoke_pass`
- manifest: `experiments/manifests/m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight.json`
- parent design: `docs/m2483-high-fidelity-interface-source-only-fixture-smoke-design.md`
- implementation: `src/autodrift/hf0_source_only_fixture_smoke.py`
- focused tests: `tests/test_hf0_source_only_fixture_smoke.py`
- summary: `runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/summary.json`
- smoke rows: `runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/fixture_smoke_rows.csv`
- next milestone: `m2485-high-fidelity-interface-source-only-fixture-smoke-result-audit`
- external high-fidelity simulation installed/imported/executed in M2484: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2484: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2484 executes the bounded source-only fixture smoke designed in M2483. It
exercises the `FourWheelHF0Backend` over the three M2482
`admitted_for_materialization` fixture rows:

```text
hf0_four_wheel_stable_aes_fixture
hf0_four_wheel_drift_required_recovery_fixture
hf0_four_wheel_unavoidable_mitigation_fixture
```

The actions are canned adapter-smoke commands. They are not policy actions and
must not be interpreted as controller performance.

## Preflight Result

The summary reports:

```text
result_class: hf0_source_only_fixture_smoke_pass
status_pass: true
backend_id: source_only_four_wheel_hf0
fixture_count: 3
admitted_source_only_fixture_count: 3
reset_count: 3
step_count: 6
observation_shape: 72
action_shape: 3
all_reset_observations_shape_72: true
all_step_observations_shape_72: true
all_action_shapes_3: true
diagnostic_wheel_force_counts: [4, 4, 4, 4, 4, 4]
canned_actions_only: true
policy_action: false
```

Role coverage:

```text
stable_aes: 1
drift_required_recovery: 1
unavoidable_mitigation: 1
```

## Contract Checks

The preflight preserves the actor/action boundary:

```text
fixture_labels_enter_actor_input: false
scenario_labels_enter_actor_input: false
feasibility_classes_enter_actor_input: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
```

Four-wheel diagnostics remain diagnostics-only:

```text
wheel forces
fault scales
vehicle params
source model state
physical controls
```

These are not consumed by `ActorView` or `P0ObservationExtractor`.

## Evidence Scope

M2484 proves only that the admitted source-only fixture rows can be smoke-tested
through the HF0 source-only adapter while preserving observation shape `72`,
action shape `3`, and metadata/diagnostics separation.

M2484 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.

## Commands

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_hf0_source_only_fixture_smoke.py
```

Result:

```text
3 passed
```

```text
PYTHONPATH=src python -m autodrift.hf0_source_only_fixture_smoke --output-dir runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight --next-blocker m2485-high-fidelity-interface-source-only-fixture-smoke-result-audit
```

Result:

```text
result_class=hf0_source_only_fixture_smoke_pass
status_pass=True
fixture_count=3
step_count=6
```

## Next

Route to
`m2485-high-fidelity-interface-source-only-fixture-smoke-result-audit`.

M2485 should audit whether M2484 is enough to route to a bounded pilot design or
whether the high-fidelity interface branch needs synthesis before more
infrastructure.
