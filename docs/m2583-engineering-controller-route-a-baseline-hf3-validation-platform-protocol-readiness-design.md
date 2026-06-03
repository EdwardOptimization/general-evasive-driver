# M2583 Engineering Controller Route A Baseline HF3 Validation Platform/Protocol Readiness Design

- status: completed
- decision: `route_to_hf3_validation_platform_protocol_readiness_materialization_preflight`
- manifest: `experiments/manifests/m2583-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-design.json`
- parent synthesis: `docs/m2582-engineering-controller-route-a-baseline-hf3-validation-admission-result-synthesis.md`
- parent audit: `docs/m2581-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-result-audit.md`
- parent materialization summary: `runs/m2580_engineering_controller_route_a_hf3_validation_admission/summary.json`
- follow-up manifest: `experiments/manifests/m2584-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-preflight.json`
- next: `m2584-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-preflight`

## Design Verdict

M2583 designs the bounded artifacts required before Route A HF3
validation-admission materialization can advance toward platform/protocol
readiness. The next milestone may materialize platform-candidate,
dependency/import-policy, validation-protocol-skeleton, source-only adapter
prerequisite, actor/action guard, claim-boundary, and gate rows.

M2583 does not select a validation platform. It does not install, import, or
run external simulation. It does not grant validation admission, validation
readiness, validation result, driver performance, rollout success, ranking,
paper evidence, current-sim verdict, finite-window-vs-GRU evidence, or
self-identification.

## Source Evidence

Accepted source boundary:

```text
M2582 synthesis decision: continue_to_hf3_validation_platform_protocol_readiness_design
M2581 audit decision: accept_hf3_validation_admission_materialization_route_to_result_synthesis
M2580 status_pass: true
admission request rows: 2
admission criteria rows: 12
external-platform readiness rows: 3
evidence-sufficiency rows: 7
actor/action guard rows: 2
claim-boundary checks: 12
materialization gates: 9/9 pass
actor contract: P0 observation 72 / action 3
allowed operational claim: validation-admission design materialized
validation admission claim: false
platform selected: false
validation execution claim: false
high-fidelity validation readiness/result claim: false
ranking/promotion/driver-performance/self-ID claim: false
external high-fidelity simulation install/import/run: false
```

M2582 identifies the remaining readiness gaps:

```text
external platform selection: missing before admission/readiness/result
validation protocol: missing before admission/readiness/result
validation execution result: missing before result
claim-boundary audit after admission: missing before readiness/result
```

## M2584 Artifact Contract

M2584 should write:

```text
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/summary.json
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_validation_platform_candidate_rows.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_validation_dependency_import_policy_rows.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_validation_protocol_skeleton_rows.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_source_only_adapter_prerequisite_rows.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_platform_protocol_actor_action_guard_rows.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/hf3_platform_protocol_claim_boundary_checks.csv
runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/validation_platform_protocol_readiness_gate_matrix.csv
docs/m2584-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-preflight.md
```

## Platform Candidate Rows

M2584 should write platform candidate rows:

```text
platform_candidate_id
platform_family
platform_role
open_auditable_backend_required
black_box_demonstration_only
repo_local_diagnostic_only
selected_for_validation_in_m2584
install_allowed_in_m2584
import_allowed_in_m2584
runtime_execution_allowed_in_m2584
dependency_mutation_allowed_in_m2584
status_pass
claim_boundary
```

Required platform families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- no platform is selected in M2584
- install/import/runtime execution are false in M2584
- dependency mutation is false in M2584
- the preferred future validation direction remains open and auditable
- black-box industry backends remain optional demonstration only
- repo-local current-sim remains diagnostic only and not validation authority

## Dependency/Import Policy Rows

M2584 should write dependency/import policy rows:

```text
dependency_policy_id
dependency_family
external_install_allowed_in_m2584
external_import_allowed_in_m2584
runtime_execution_allowed_in_m2584
dependency_mutation_allowed_in_m2584
future_readiness_design_allowed_after_audit
status_pass
claim_boundary
```

Required dependency families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- external install/import/runtime execution are false in M2584
- dependency mutation is false in M2584
- future readiness design is allowed only after audit and without execution
- no dependency row may imply validation readiness or result

## Validation Protocol Skeleton Rows

M2584 should write two protocol skeleton rows:

```text
validation_protocol_id
admission_request_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
protocol_skeleton_defined
holdout_or_generalization_policy_defined
reset_allowed_in_m2584
policy_action_allowed_in_m2584
environment_step_allowed_in_m2584
rollout_allowed_in_m2584
external_validation_execution_allowed_in_m2584
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_validation_platform_protocol_skeleton`
- `stable_aes_aeb_infeasible_validation_platform_protocol_skeleton`

Pass criteria:

- exactly two rows exist
- both rows map to accepted M2580 admission request rows
- both rows preserve P0 `72/3`
- protocol skeleton is defined as a static contract only
- holdout/generalization policy remains not defined in M2584
- reset/action/step/rollout/external validation execution are false in M2584
- validation result claims remain false

## Source-Only Adapter Prerequisite Rows

M2584 should write source-only adapter prerequisite rows:

```text
adapter_prerequisite_id
prerequisite_family
required_before_external_execution
satisfied_in_m2584
missing_before_platform_protocol_readiness
status_pass
claim_boundary
```

Required prerequisite families:

- `p0_observation_shape_contract`
- `deployed_action_mapping_contract`
- `metadata_only_scenario_label_policy`
- `external_state_extraction_boundary`
- `time_step_and_actuator_latency_contract`
- `failure_status_taxonomy_mapping`
- `source_only_fixture_smoke_lineage`

Pass criteria:

- satisfied rows may include only already-established source-side contracts
- external state extraction, time-step/latency, failure/status mapping, and
  source-only fixture-smoke lineage remain missing before platform/protocol
  readiness if not explicitly proven by M2584 artifacts
- missing prerequisites must not be interpreted as validation readiness

## Actor/Action Guard Rows

M2584 should write actor/action guard rows:

```text
actor_action_guard_id
admission_request_id
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

M2584 should write claim-boundary rows for:

- platform/protocol readiness design materialized
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

Only the operational claim `platform/protocol readiness design materialized` may
become true after M2584 if all design materialization rows pass. Platform
selection, validation protocol readiness, validation admission, validation
readiness/result, external execution, HF4 discrepancy result, rollout success,
ranking, promotion, success rate, driver performance, paper evidence, and
self-ID remain false.

## Gate Matrix

M2584 should pass only if:

```text
source_artifacts_exist
platform_candidate_rows_complete
dependency_import_policy_rows_pass
validation_protocol_skeleton_rows_pass
source_only_adapter_prerequisite_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_platform_selected_or_external_execution
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, actor input mutation, action contract mutation, reset execution,
policy action, environment step, rollout execution, validation execution,
training, replay, PPO, ranking, winner selection, checkpoint promotion,
success-rate computation, platform-selection claim, validation admission claim,
validation readiness claim, validation result claim, rollout success claim,
driver-performance claim, paper claim, finite-window-vs-GRU claim, current-sim
verdict claim, high-fidelity validation claim, HF4 discrepancy result claim, and
self-ID claim.

## Follow-Up

Route to M2584 validation platform/protocol readiness materialization preflight.
M2584 should materialize static platform/protocol readiness design artifacts
only. If M2584 passes, the next task should audit the materialization before any
platform selection, external dependency preparation, or validation execution
design is selected.
