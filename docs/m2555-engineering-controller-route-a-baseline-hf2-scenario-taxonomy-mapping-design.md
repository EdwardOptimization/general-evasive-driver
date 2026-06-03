# M2555 Engineering Controller Route A Baseline HF2 Scenario Taxonomy Mapping Design

- status: completed
- decision: `route_to_hf2_scenario_taxonomy_mapping_materialization_preflight`
- manifest: `experiments/manifests/m2555-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-design.json`
- parent synthesis: `docs/m2554-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-result-synthesis.md`
- HF1 boundary source: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json`
- taxonomy source: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv`
- fixture source: `runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv`
- follow-up manifest: `experiments/manifests/m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight.json`
- next: `m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight`

## Scope

M2555 designs the Route A HF2 scenario taxonomy mapping materialization after
accepted HF1 P0 parity-smoke evidence. The design prepares M2556 to write
machine-readable artifacts that bind Route C role families to existing
surface/fixture rows while preserving actor boundary and support-status
honesty.

M2555 is design-only. It does not install, import, or run external
high-fidelity simulation. It does not execute policy actions, step
environments, train, replay, rank, promote, compute success rates, or claim
validation or driver performance.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines HF2 scenario taxonomy mapping as:

```text
stable avoidable / AEB-feasible
stable AES / AEB-infeasible
drift-required recovery
hidden-dynamics robustness
unavoidable mitigation
```

M2556 should materialize these as metadata role rows only. The actor must not
receive scenario labels, feasibility classes, AEB/AES labels, pilot admission
labels, or any oracle readiness values.

## Source Contracts

M2556 should bind to the accepted HF1 contract:

```text
P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
diagnostic-only keys checked by M2552 = 33
HF1 actor-visible P0 coverage = 72/72
```

M2556 should reuse M2480/M2482 as source material only:

```text
M2480 surfaces: current_sim_autodrift_hf0, source_only_four_wheel_hf0
M2480 roles: stable_avoidable, stable_aes, drift_required_recovery,
             hidden_dynamics_robustness, unavoidable_mitigation
M2480 support status: supported=5, limited_fixture=5
M2482 fixture catalog rows: 10
M2482 admitted source-only fixtures: 3
M2482 current-sim limited references: 2
```

Existing support/admission status must be preserved. M2556 may create Route
A/HF2 bindings, but it must not silently promote `limited_fixture`,
`diagnostic_reference_only`, or `baseline_reference` rows to pilot-ready rows.

## M2556 Required Artifacts

M2556 should write:

```text
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_route_role_mapping.csv
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_surface_fixture_binding.csv
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_metadata_boundary_checks.csv
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_pilot_admission_guard_rows.csv
runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/materialization_gate_matrix.csv
docs/m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight.md
```

## Route Role Mapping

M2556 should write one row per HF2 route role:

```text
route_role_id
route_role_label
m2480_role_family
route_c_family
actor_observation_shape
action_shape
actor_visible_allowed_fields
metadata_only_labels
feasibility_label_actor_visible
pilot_admission_allowed_by_mapping
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible`
- `stable_aes_aeb_infeasible`
- `drift_required_recovery`
- `hidden_dynamics_robustness`
- `unavoidable_mitigation`

Pass criteria:

- every Route C family is represented exactly once
- P0 shape remains `72` and action shape remains `3`
- feasibility labels are metadata-only
- role labels do not enter actor-visible fields
- no route role is claimed as validation or performance evidence

## Surface/Fixture Binding

M2556 should join M2480 surface-role rows to M2482 fixture catalog rows and
write binding rows:

```text
binding_id
route_role_id
surface_id
m2480_role_family
m2480_support_status
m2482_fixture_id
m2482_fixture_admission_status
actor_observation_shape
action_shape
binding_status
support_status_preserved
limited_or_reference_upgraded
status_pass
claim_boundary
```

Binding policy:

- `supported` rows may bind as `reference_binding` or `baseline_binding`.
- `limited_fixture` rows may bind as `limited_fixture_binding`.
- `diagnostic_reference_only` rows remain diagnostic references.
- `admitted_for_materialization` rows remain materialization candidates, not
  HF3 pilot admission.
- missing fixture rows must be reported as `blocked_binding`, not fabricated.

Pass criteria:

- every M2480 surface/role row has an honest binding status
- no limited/reference row is silently upgraded
- P0 `72/3` is preserved in every row
- no binding row leaks labels or oracle feasibility into actor input

## Metadata Boundary Checks

M2556 should write rows for label and metadata families:

```text
metadata_family
example_fields
source_artifact
actor_visible_allowed
present_in_actor_field_map
hidden_or_oracle_risk
status_pass
claim_boundary
```

Required metadata families:

- scenario role labels
- feasibility labels
- AEB/AES feasibility labels
- current-sim hidden/task fields
- source-only four-wheel hidden dynamics fields
- fixture admission labels
- success/reward/termination labels

Pass criteria:

- all metadata families are checked
- none are actor-visible
- hidden dynamics, force/slip/load details, labels, rewards, TTC-like values,
  and success/progress signals remain outside actor input

## Pilot Admission Guards

M2556 should write guard rows that explicitly prevent HF3 pilot admission from
taxonomy metadata alone:

```text
guard_id
route_role_id
source_binding_status
pilot_candidate_status
required_before_hf3
pilot_admission_claim_made
status_pass
claim_boundary
```

Pass criteria:

- no role is admitted to HF3 pilot by M2556 alone
- stable avoidable and stable AES rows list missing materialized pilot
  readiness conditions
- limited/reference roles remain blocked or conditional
- no success-rate, validation, controller-family, or driver-performance claim
  is made

## Gate Matrix

M2556 passes only if:

- all required artifacts exist
- all five Route C role families are mapped
- every M2480/M2482 source row is represented or explicitly blocked
- support/admission status is preserved without silent upgrade
- metadata boundary checks pass
- pilot admission guards prevent HF3 promotion from taxonomy metadata alone
- P0 observation shape `72` and action shape `3` are preserved
- no external simulator install/import/run occurs
- no policy rollout, training, replay, PPO, ranking, winner selection,
  checkpoint promotion, success-rate, validation, driver-performance, paper,
  FW-vs-GRU, current-sim, high-fidelity validation, or self-ID claim is made

## Follow-Up

Route to M2556 materialization/preflight. M2556 may add a bounded source-only
materializer and tests to write the artifacts above. It must not run external
high-fidelity simulation, step environments, or interpret taxonomy rows as
driver performance.
