# M2480 High-Fidelity Interface Scenario Taxonomy Mapping Materialization Preflight

- status: completed
- result_class: `hf0_scenario_taxonomy_mapping_materialization_pass`
- manifest: `experiments/manifests/m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight.json`
- parent design: `docs/m2479-high-fidelity-interface-scenario-taxonomy-mapping-design.md`
- implementation: `src/autodrift/hf0_scenario_taxonomy_mapping.py`
- focused tests: `tests/test_hf0_scenario_taxonomy_mapping.py`
- summary: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json`
- matrix: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv`
- next milestone: `m2481-high-fidelity-interface-scenario-taxonomy-fixture-design`
- external high-fidelity simulation installed/imported/executed in M2480: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2480: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2480 materializes the M2479 HF0 scenario taxonomy mapping into checked
machine-readable artifacts. The goal is to make the next fixture work explicit
without letting scenario role labels, feasibility classes, hidden dynamics, or
diagnostics enter the deployable actor input.

The actor/action contract remains:

```text
actor observation shape: 72
actor action shape: 3
actor-visible extraction source: ActorView only
```

## Materialized Matrix

The generated matrix covers:

```text
surfaces:
  current_sim_autodrift_hf0
  source_only_four_wheel_hf0

role families:
  stable_avoidable
  stable_aes
  drift_required_recovery
  hidden_dynamics_robustness
  unavoidable_mitigation

row count: 10
```

Support-status counts:

```text
supported: 5
limited_fixture: 5
blocked: 0
```

Current-sim rows mark `stable_aes` and `unavoidable_mitigation` as
`limited_fixture`, because stable-AES reset-ready support remains partial and
unavoidable feasibility is oracle metadata. Source-only four-wheel rows mark
`stable_aes`, `drift_required_recovery`, and `unavoidable_mitigation` as
`limited_fixture`, because that adapter currently has deterministic road and
obstacle fixtures rather than role-specific scenario families.

## Contract Checks

The summary reports:

```text
status_pass: true
actor_observation_shape: 72
action_shape: 3
all_rows_preserve_observation_shape: true
all_rows_preserve_action_shape: true
scenario_labels_enter_actor_input: false
feasibility_classes_enter_actor_input: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
actor_metadata_leaks: {}
```

Actor-visible fields remain limited to:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road boundary geometry
ego-frame obstacle geometry and relative motion
```

Metadata-only fields include scenario role labels, feasibility classes,
current-sim hidden parameters, oracle clearance/termination labels, four-wheel
vehicle params, fault scales, per-wheel forces, and slip/load-like diagnostics.

## Evidence Scope

M2480 is taxonomy materialization/preflight only. It supports bounded fixture
design by making surface-role support status explicit.

M2480 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.

## Commands

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_hf0_scenario_taxonomy_mapping.py
```

Result:

```text
4 passed
```

```text
PYTHONPATH=src python -m autodrift.hf0_scenario_taxonomy_mapping --output-dir runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight --next-blocker m2481-high-fidelity-interface-scenario-taxonomy-fixture-design
```

Result:

```text
result_class=hf0_scenario_taxonomy_mapping_materialization_pass
status_pass=True
row_count=10
```

## Next

Route to
`m2481-high-fidelity-interface-scenario-taxonomy-fixture-design`.

M2481 should design bounded fixture work for the limited role rows, especially
source-only four-wheel `stable_aes`, `drift_required_recovery`, and
`unavoidable_mitigation`, while preserving observation shape `72`, action shape
`3`, and the metadata-only role/feasibility boundary.
