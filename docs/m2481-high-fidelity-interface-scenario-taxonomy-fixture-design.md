# M2481 High-Fidelity Interface Scenario Taxonomy Fixture Design

- status: completed
- decision: `scenario_taxonomy_fixture_design_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2481-high-fidelity-interface-scenario-taxonomy-fixture-design.json`
- parent summary: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json`
- parent matrix: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv`
- next milestone: `m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight`
- external high-fidelity simulation installed/imported/executed in M2481: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2481: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2481 designs the bounded fixture requirements that should follow the M2480
surface-role matrix. This is still HF0 interface preparation, not validation.

The route constraint from `docs/post-m2470-route-plan.md` remains active:
current-sim is a diagnostic/mining layer and should not regain control of the
main loop through another stable-AES static repair chain. Therefore M2481
routes limited rows into a fixture catalog materialization step, not into
current-sim micro-repair or controller ranking.

## Inputs

M2480 materialized:

```text
surface count: 2
role count: 5
row count: 10
support statuses:
  supported: 5
  limited_fixture: 5
  blocked: 0
observation/action shape: 72 / 3
scenario labels enter actor input: false
feasibility classes enter actor input: false
hidden/oracle values enter actor input: false
```

Limited rows requiring fixture design:

```text
current_sim_autodrift_hf0:
  stable_aes
  unavoidable_mitigation

source_only_four_wheel_hf0:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation
```

## Fixture Admission Policy

Each fixture row must preserve:

```text
actor_observation_shape: 72
action_shape: 3
actor-visible source: ActorView only
scenario role labels: metadata only
feasibility classes: metadata only
hidden dynamics and wheel diagnostics: metadata only
oracle unavoidable/clearance verdicts: metadata only
```

Allowed actor-visible channels remain:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road boundary geometry
ego-frame obstacle geometry and relative motion
```

Forbidden actor-visible channels include:

```text
scenario role label
AEB/AES/drift/unavoidable feasibility class
mu, mass, CG, tire/brake/drive/actuator scales
wheel forces, slip/load-like diagnostics, fault scales
TTC, stopping distance, required clearance
reward terms, success labels, termination labels
```

## Designed Fixture Rows

The M2482 materialization should produce a fixture catalog with these rows:

```text
fixture_id: hf0_current_sim_stable_aes_reference
surface: current_sim_autodrift_hf0
role: stable_aes
admission: diagnostic_reference_only
reason: stable-AES reset-ready support remains partial; do not restart static
        current-sim support repair without synthesis approval
next check: keep as reference metadata, not as pilot admission

fixture_id: hf0_current_sim_unavoidable_mitigation_reference
surface: current_sim_autodrift_hf0
role: unavoidable_mitigation
admission: diagnostic_reference_only
reason: unavoidable feasibility is oracle metadata
next check: define mitigation metrics only after fixture catalog materializes

fixture_id: hf0_four_wheel_stable_aes_fixture
surface: source_only_four_wheel_hf0
role: stable_aes
admission: admitted_for_materialization
reason: source-only adapter can expose obstacle geometry and vehicle response
        without exposing feasibility labels
next check: materialize deterministic evasive-steering fixture metadata

fixture_id: hf0_four_wheel_drift_required_recovery_fixture
surface: source_only_four_wheel_hf0
role: drift_required_recovery
admission: admitted_for_materialization
reason: four-contact-patch dynamics can support recovery fixture definitions,
        while wheel forces/fault scales remain diagnostics-only
next check: materialize recovery fixture metadata and backend reset options

fixture_id: hf0_four_wheel_unavoidable_mitigation_fixture
surface: source_only_four_wheel_hf0
role: unavoidable_mitigation
admission: admitted_for_materialization
reason: mitigation role can be represented as metadata-side fixture objective
        without exposing oracle unavoidable labels
next check: materialize mitigation fixture metadata with actor contract checks
```

Supported rows from M2480 should also appear in the M2482 catalog as
`baseline_reference` entries so that the catalog remains complete across all
two surfaces and five role families. The implementation should not fabricate
support for limited rows; it should carry the admission status explicitly.

## M2482 Materialization Requirements

M2482 should add:

```text
src/autodrift/hf0_scenario_taxonomy_fixtures.py
tests/test_hf0_scenario_taxonomy_fixtures.py
runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json
runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv
```

The summary must report:

```text
catalog row count
surface count
role count
admission status counts
all rows preserve observation shape 72
all rows preserve action shape 3
scenario labels enter actor input: false
feasibility classes enter actor input: false
hidden/oracle values enter actor input: false
external simulation/import/training/ranking/winner/verdict flags: false
```

## Evidence Scope

M2481 is fixture design only. It supports a bounded materialization/preflight
step for a fixture catalog.

M2481 does not prove high-fidelity validation readiness, driver performance,
current-sim benchmark readiness, finite-window-vs-GRU evidence, or level-3
self-identification.

## Next

Route to
`m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight`.
