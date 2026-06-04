# M2595 Engineering Controller Route A Baseline HF3 Platform/Protocol Readiness After Source-Only Closure Design

- status: completed
- decision: `route_to_hf3_platform_protocol_readiness_after_source_only_closure_materialization_preflight`
- manifest: `experiments/manifests/m2595-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-design.json`
- parent synthesis: `docs/m2594-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-result-synthesis.md`
- parent audit: `docs/m2593-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-result-audit.md`
- parent closure summary: `runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json`
- follow-up manifest: `experiments/manifests/m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-preflight.json`
- next: `m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-preflight`

## Design Verdict

M2595 designs the bounded artifacts required to rematerialize Route A HF3
platform/protocol readiness after source-only adapter blocker closure. M2596
should materialize after-closure platform candidates, dependency/import policy,
validation protocol skeleton, source-only closure evidence, actor/action guard,
claim-boundary, and gate rows.

This design is intentionally still pre-validation. It does not select a
validation platform, install or import external simulation dependencies, run
external simulation, execute resets, execute policy actions, step environments,
execute rollouts, execute validation, train, rank controllers, promote
checkpoints, compute success rates, or claim driver performance.

If M2596 passes all gates, the allowed claim is limited to after-closure
platform/protocol readiness design artifacts materialized. That would still not
imply platform selection, validation protocol readiness, validation admission,
high-fidelity validation readiness, validation result, HF4 discrepancy result,
current-sim verdict, paper-level evidence, finite-window-vs-GRU evidence,
level3 self-ID, or professional driver behavior.

## Source Evidence

Accepted source boundary:

```text
M2594 synthesis decision: continue_to_hf3_platform_protocol_readiness_after_source_only_closure_design
M2593 audit decision: accept_hf3_source_only_adapter_blocker_closure_materialization_route_to_result_synthesis
M2592 status_pass: true
external-state extraction closure rows: 4/4 pass
time-step/actuator latency closure rows: 4/4 pass
failure/status taxonomy closure rows: 4/4 pass
source-only fixture smoke closure rows: 4/4 pass
actor-visibility guard rows: 4/4 pass
claim-boundary checks: 15/15 pass
materialization gates: 13/13 pass
repo_local_source_only_adapter_blocker_closure_materialized: true
validation_protocol_ready_in_m2592: false
external_validation_execution_allowed_in_m2592: false
platform_selected_in_m2592: false
driver_performance_claim_allowed_in_m2592: false
actor contract: P0 observation 72 / action 3
```

M2584 previously represented platform/protocol skeleton artifacts while four
source-only adapter prerequisites remained missing. M2592/M2593/M2594 close
that specific source-only prerequisite gap in repo-local evidence, which allows
M2596 to rematerialize the platform/protocol readiness panel with after-closure
source evidence.

## M2596 Artifact Contract

M2596 should write:

```text
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/summary.json
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_platform_candidate_rows.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_dependency_import_policy_rows.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_validation_protocol_skeleton_rows.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_source_only_evidence_rows.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_actor_action_guard_rows.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/hf3_after_closure_claim_boundary_checks.csv
runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/after_closure_platform_protocol_readiness_gate_matrix.csv
docs/m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-preflight.md
```

Every M2596 row should prove platform/protocol readiness design artifacts only
after source-only closure. Rows must keep:

```text
source_only_closure_accepted_in_m2596: true
platform_selected_in_m2596: false
validation_protocol_ready_in_m2596: false
validation_admission_granted_in_m2596: false
external_validation_execution_allowed_in_m2596: false
driver_performance_claim_allowed_in_m2596: false
```

## Platform Candidate Rows

M2596 should write after-closure platform candidate rows:

```text
platform_candidate_id
platform_family
platform_role
source_only_closure_required_before_selection
source_only_closure_accepted_in_m2596
open_auditable_backend_required
black_box_demonstration_only
repo_local_diagnostic_only
selected_for_validation_in_m2596
install_allowed_in_m2596
import_allowed_in_m2596
runtime_execution_allowed_in_m2596
dependency_mutation_allowed_in_m2596
status_pass
claim_boundary
```

Required platform families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- no platform is selected in M2596
- install/import/runtime execution are false in M2596
- dependency mutation is false in M2596
- source-only closure is accepted as a prerequisite, not as platform selection
- the preferred future validation direction remains open and auditable
- black-box industry backends remain optional demonstration only
- repo-local current-sim remains diagnostic only and not validation authority

## Dependency/Import Policy Rows

M2596 should write dependency/import policy rows:

```text
dependency_policy_id
dependency_family
source_only_closure_accepted_in_m2596
external_install_allowed_in_m2596
external_import_allowed_in_m2596
runtime_execution_allowed_in_m2596
dependency_mutation_allowed_in_m2596
future_platform_selection_design_allowed_after_audit
status_pass
claim_boundary
```

Pass criteria:

- external install/import/runtime execution are false in M2596
- dependency mutation is false in M2596
- future platform-selection design is allowed only after audit and without
  execution
- no dependency row may imply validation readiness or result

## Validation Protocol Skeleton Rows

M2596 should write protocol skeleton rows:

```text
validation_protocol_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
source_only_closure_accepted_in_m2596
protocol_skeleton_defined
holdout_or_generalization_policy_defined
reset_allowed_in_m2596
policy_action_allowed_in_m2596
environment_step_allowed_in_m2596
rollout_allowed_in_m2596
external_validation_execution_allowed_in_m2596
validation_protocol_ready_in_m2596
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_after_closure_protocol_skeleton`
- `stable_aes_aeb_infeasible_after_closure_protocol_skeleton`

Pass criteria:

- exactly two rows exist
- both rows preserve P0 `72/3`
- protocol skeleton is defined as a static contract only
- holdout/generalization policy remains not defined in M2596
- reset/action/step/rollout/external validation execution are false in M2596
- validation protocol readiness and result claims remain false

## Source-Only Closure Evidence Rows

M2596 should write source-only closure evidence rows:

```text
closure_evidence_id
closure_family
source_artifact
closure_materialized_in_m2592
closure_audited_in_m2593
accepted_by_m2594_synthesis
required_before_external_execution
missing_after_source_only_closure
status_pass
claim_boundary
```

Required closure families:

- `external_state_extraction_boundary`
- `time_step_and_actuator_latency_contract`
- `failure_status_taxonomy_mapping`
- `source_only_fixture_smoke_lineage`

Pass criteria:

- every source-only closure family is materialized, audited, and accepted by
  synthesis
- no closure evidence row is missing after source-only closure
- closure evidence rows support after-closure platform/protocol readiness
  design artifacts only, not platform selection or validation result

## Actor/Action Guard Rows

M2596 should write actor/action guard rows:

```text
actor_action_guard_id
route_role_id
actor_observation_shape
action_shape
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
rollout_outcome_actor_visible
validation_outcome_actor_visible
platform_selection_actor_visible
protocol_status_actor_visible
action_contract_mutation_detected
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- hidden/oracle, diagnostics, labels, backend status, reset outcome, rollout
  outcome, validation outcome, platform selection, and protocol status are
  false for actor-visible inputs
- action contract mutation is false

## Claim Boundary Checks

M2596 should write claim-boundary rows for:

- after-closure platform/protocol readiness design materialized
- platform selected for validation
- validation protocol ready
- validation admission granted
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- HF4 discrepancy result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

Only the operational claim
`after_closure_platform_protocol_readiness_design_materialized` may become true
after M2596 if all design materialization rows pass. Platform selection,
validation protocol readiness, validation admission, validation readiness/result,
external execution, HF4 discrepancy result, rollout success, ranking, promotion,
success rate, driver performance, paper evidence, and self-ID remain false.

## Gate Matrix

M2596 should pass only if:

```text
source_artifacts_exist
m2592_closure_evidence_accepted
platform_candidate_rows_complete
dependency_import_policy_rows_pass
validation_protocol_skeleton_rows_pass
source_only_closure_evidence_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_platform_selected_or_external_execution
validation_readiness_and_result_forbidden
no_forbidden_execution_or_claim_flags
```

The expected result class is:

```text
engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure_materialization_preflight_pass
```

## Follow-Up

Register and run:

```text
m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-preflight
```

M2596 may materialize after-closure platform/protocol readiness design
artifacts. It must not select a platform, install/import/run external
simulation, execute reset/action/step, run rollouts or validation, train, rank,
promote, compute success rates, or claim validation readiness/result or driver
performance.
