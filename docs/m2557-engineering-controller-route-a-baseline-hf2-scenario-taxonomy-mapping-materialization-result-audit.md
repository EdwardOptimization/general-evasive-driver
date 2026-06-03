# M2557 Engineering Controller Route A Baseline HF2 Scenario Taxonomy Mapping Materialization Result Audit

- status: completed
- decision: `accept_hf2_scenario_taxonomy_mapping_route_to_result_synthesis`
- manifest: `experiments/manifests/m2557-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-result-audit.json`
- parent summary: `runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json`
- parent doc: `docs/m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis.json`
- next: `m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis`

## Audit Verdict

M2557 accepts M2556 as source-level Route A HF2 scenario taxonomy mapping
materialization evidence. The accepted claim is narrow: Route C role families
are mapped, surface/fixture bindings preserve M2480/M2482 support/admission
status, metadata labels remain outside actor input, and pilot-admission guards
prevent HF3 pilot claims from taxonomy metadata alone.

M2557 does not accept high-fidelity validation readiness/result,
driver-performance claim, controller ranking, checkpoint promotion, success
rate, paper evidence, finite-window-vs-GRU result, current-sim verdict, or
level3 self-identification claim.

## Evidence Checks

Accepted M2556 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization_pass
source_artifacts_exist: true
route_role_mapping_row_count: 5
surface_fixture_binding_row_count: 10
metadata_boundary_check_count: 7
pilot_admission_guard_count: 5
materialization_gate_count: 7
materialization_gates_all_pass: true
observation_shape: 72
action_shape: 3
source support counts: supported=5, limited_fixture=5
binding counts: baseline_reference=5, diagnostic_reference=2, materialization_candidate=3
limited_or_reference_upgraded: false
metadata_labels_enter_actor_input: false
pilot_admission_claim_made: false
hidden_oracle_actor_input_detected: false
```

Required artifact audit:

```text
summary.json: present
hf2_route_role_mapping.csv: present
hf2_surface_fixture_binding.csv: present
hf2_metadata_boundary_checks.csv: present
hf2_pilot_admission_guard_rows.csv: present
materialization_gate_matrix.csv: present
milestone doc: present
```

Gate audit:

```text
source_artifacts_exist: pass
route_role_mapping_complete: pass
surface_fixture_bindings_complete: pass
metadata_boundary_checks_pass: pass
pilot_admission_guards_pass: pass
actor_action_contract_preserved: pass
no_false_claim_flags: pass
```

## Supported Claims

Supported:

- HF2 taxonomy mapping artifacts are materialized for Route A
- all five Route C role families are represented
- all ten M2480/M2482 source surface/fixture bindings are represented
- support/admission statuses are preserved without silent upgrade
- metadata-only labels and feasibility classes remain outside actor input
- pilot-admission guard rows prevent HF3 pilot readiness claims from M2556
- the branch is ready for a bounded result synthesis before deciding HF3 pilot
  design, repair, pivot, or stop

## Rejected Claims

Not supported:

- high-fidelity validation readiness or result
- external simulator behavior transfer
- HF3 pilot admission
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

The earlier mitigation-proof limitation remains unresolved. M2556/M2557 do not
repair driver behavior, run closed-loop policy rollouts, or evaluate scenario
success.

## Failure Taxonomy

No M2556/M2557 failure is accepted for:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this taxonomy route.
- `objective_overfit`: taxonomy metadata must not be used as ranking,
  validation, or public-gate tuning evidence.
- `scenario_sampling_failure`: not triggered here, but HF3 pilot design must
  use reset/rollout feasibility gates rather than taxonomy metadata alone.

## Next Route

Route to:

```text
m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis
```

M2558 should synthesize M2556/M2557 and decide whether to continue to HF3
low-cost pilot design, repair a taxonomy artifact/contract/mapping issue,
pivot, or stop. It must not claim validation or driver performance.
