# M2483 High-Fidelity Interface Source-Only Fixture Smoke Design

- status: completed
- decision: `source_only_fixture_smoke_design_route_to_implementation_preflight`
- manifest: `experiments/manifests/m2483-high-fidelity-interface-source-only-fixture-smoke-design.json`
- parent catalog: `runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv`
- parent summary: `runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json`
- source-only adapter: `src/autodrift/four_wheel_hf0_adapter.py`
- next milestone: `m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight`
- external high-fidelity simulation installed/imported/executed in M2483: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2483: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2483 designs a bounded executable smoke protocol for the three source-only
fixture rows that M2482 admitted for materialization:

```text
hf0_four_wheel_stable_aes_fixture
hf0_four_wheel_drift_required_recovery_fixture
hf0_four_wheel_unavoidable_mitigation_fixture
```

This is still HF0 infrastructure. It is not high-fidelity validation, current-
sim verdict evidence, driver capability evidence, controller-family ranking,
or a paper-level result.

## Smoke Protocol

M2484 should implement a preflight that:

```text
1. Loads/builds the M2482 fixture catalog rows.
2. Selects only rows with:
   surface_id = source_only_four_wheel_hf0
   fixture_admission_status = admitted_for_materialization
3. Resets FourWheelHF0Backend once per admitted fixture row.
4. Executes a tiny canned action sequence per row.
5. Extracts P0 observations through P0ObservationExtractor.
6. Verifies every reset and step observation has shape 72.
7. Verifies every action has shape 3 and uses the existing action validator.
8. Verifies wheel forces/fault scales/model state remain diagnostics-only.
9. Verifies fixture_id, role_family, feasibility class, and admission status
   remain artifact metadata and backend_info only, not ActorView/P0 input.
10. Emits a summary JSON and fixture_smoke_rows.csv.
```

Allowed canned action sequences:

```text
stable_aes:
  (0.35, -0.20, -0.80)
  (-0.15, -0.15, -0.65)

drift_required_recovery:
  (0.55, 0.10, -0.75)
  (-0.35, -0.10, -0.55)

unavoidable_mitigation:
  (0.10, -0.35, -0.20)
  (0.00, -0.50, 0.10)
```

These are not policy actions and must not be interpreted as controller
performance. They only exercise the adapter boundary under role-tagged fixture
metadata.

## Guardrails

M2484 must preserve:

```text
actor_observation_shape: 72
action_shape: 3
actor-visible source: ActorView only
scenario role labels: metadata only
fixture admission status: metadata only
feasibility classes: metadata only
hidden dynamics and wheel diagnostics: diagnostics only
oracle unavoidable/clearance verdicts: metadata only
```

Forbidden M2484 claims:

```text
high-fidelity validation readiness
driver performance
current-sim benchmark readiness
controller-family ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
```

## M2484 Implementation Requirements

M2484 should add:

```text
src/autodrift/hf0_source_only_fixture_smoke.py
tests/test_hf0_source_only_fixture_smoke.py
runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/summary.json
runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/fixture_smoke_rows.csv
docs/m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight.md
```

Minimum summary fields:

```text
status_pass
result_class
fixture_count
admitted_source_only_fixture_count
reset_count
step_count
observation_shape
action_shape
all_reset_observations_shape_72
all_step_observations_shape_72
diagnostic_wheel_force_counts
scenario_labels_enter_actor_input
feasibility_classes_enter_actor_input
fixture_labels_enter_actor_input
hidden_values_enter_actor_input
oracle_labels_enter_actor_input
policy_rollout_run
training_run
ranking_run
winner_selected
verdict_claim_made
```

## Evidence Scope

M2483 is smoke design only. It supports one bounded executable preflight over
the source-only four-wheel adapter.

M2483 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.
