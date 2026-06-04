# M2599 Engineering Controller Route A Baseline HF3 After-Closure Platform Selection Design

- status: completed
- decision: `route_to_hf3_after_closure_platform_selection_criteria_materialization_preflight`
- manifest: `experiments/manifests/m2599-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-design.json`
- parent synthesis: `docs/m2598-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-result-synthesis.md`
- parent audit: `docs/m2597-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-result-audit.md`
- parent materialization summary: `runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure/summary.json`
- follow-up manifest: `experiments/manifests/m2600-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-preflight.json`
- next: `m2600-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-preflight`

## Design Verdict

M2599 designs the bounded after-closure HF3 platform-selection criteria
artifacts required before any actual platform selection can be proposed. M2600
should materialize criteria, auditability, dependency/import risk,
validation-role compatibility, actor/action guard, claim-boundary, and gate
rows.

This design is intentionally not a platform-selection result. It does not
install or import external simulator dependencies, run high-fidelity
simulation, execute resets, execute policy actions, step environments, execute
rollouts, execute validation, train, rank controllers, promote checkpoints,
compute success rates, or claim driver performance.

If M2600 passes all gates, the allowed claim is limited to after-closure
platform-selection criteria materialized. That would still not imply platform
selection, validation protocol readiness, validation admission, high-fidelity
validation readiness, validation result, HF4 discrepancy result, current-sim
verdict, paper-level evidence, finite-window-vs-GRU evidence, level3 self-ID,
or professional driver behavior.

## Source Evidence

Accepted after-closure source boundary:

```text
M2598 synthesis decision: continue_to_hf3_after_closure_platform_selection_design
M2597 audit decision: accept_hf3_after_closure_platform_protocol_readiness_materialization_route_to_result_synthesis
M2596 status_pass: true
platform candidate rows: 3/3 pass
dependency/import policy rows: 3/3 pass
validation protocol skeleton rows: 2/2 pass
source-only closure evidence rows: 4/4 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 14/14 pass
materialization gates: 12/12 pass
source_only_closure_accepted_in_m2596: true
source_only_closure_missing_after_m2596: false
platform_selected_in_m2596: false
validation_protocol_ready_in_m2596: false
external_validation_execution_allowed_in_m2596: false
driver_performance_claim_allowed_in_m2596: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` requires the preferred validation
direction to remain an open, auditable high-fidelity vehicle dynamics layer
such as Chrono/Chrono::Vehicle, while black-box simulators remain optional
demonstration or industry-facing validation only. Current-sim remains a fast
diagnostic and adapter-contract source, not validation authority.

M2596/M2597/M2598 are enough to design selection criteria because the
source-only closure prerequisites and after-closure platform/protocol skeletons
are materialized and audited. They are not enough to select a platform.

## M2600 Artifact Contract

M2600 should write:

```text
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_criteria_rows.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_auditability_rows.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_dependency_import_risk_rows.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_validation_role_compatibility_rows.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_actor_action_guard_rows.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/hf3_after_closure_platform_selection_claim_boundary_checks.csv
runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/after_closure_platform_selection_criteria_gate_matrix.csv
docs/m2600-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-preflight.md
```

Every M2600 row should prove criteria materialization only. Rows must keep:

```text
platform_selection_criteria_materialized_in_m2600: true
platform_selected_in_m2600: false
selection_decision_allowed_in_m2600: false
validation_protocol_ready_in_m2600: false
validation_admission_granted_in_m2600: false
external_validation_execution_allowed_in_m2600: false
driver_performance_claim_allowed_in_m2600: false
```

## Platform Selection Criteria Rows

M2600 should write platform-selection criteria rows:

```text
criteria_id
platform_family
selection_role
open_auditable_backend_required
source_or_equivalent_trace_required
deterministic_reset_step_api_required
time_step_contract_required
actuator_latency_contract_required
state_extraction_boundary_required
failure_status_taxonomy_required
scenario_role_support_required
black_box_demonstration_only
repo_local_diagnostic_only
selected_for_validation_in_m2600
selection_decision_allowed_in_m2600
status_pass
claim_boundary
```

Required platform families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- exactly three platform families are represented
- the open/equivalent backend row requires auditable source or equivalent
  model/API traceability
- the black-box row is demonstration-only and not validation authority
- the repo-local current-sim row is diagnostic-only and not validation
  authority
- no row selects a platform
- no row allows validation execution or readiness/result claims

## Auditability Rows

M2600 should write auditability rows:

```text
auditability_id
platform_family
source_or_model_auditable
adapter_contract_traceable
reset_step_determinism_auditable
state_extraction_boundary_auditable
failure_status_mapping_auditable
validation_authority_allowed_after_future_selection
demonstration_only
diagnostic_only
status_pass
claim_boundary
```

Pass criteria:

- the preferred open/equivalent backend can become validation authority only
  after future platform selection and protocol-readiness audits
- black-box backends remain demonstration-only even if they have useful
  industry-facing value
- repo-local current-sim remains diagnostic-only and cannot become high-fidelity
  validation authority in M2600
- auditability rows do not expose backend status, platform selection, or
  protocol status to the actor

## Dependency/Import Risk Rows

M2600 should write dependency/import risk rows:

```text
dependency_risk_id
platform_family
external_install_allowed_in_m2600
external_import_allowed_in_m2600
runtime_execution_allowed_in_m2600
dependency_mutation_allowed_in_m2600
license_or_api_review_required_before_install
source_build_or_adapter_probe_required_before_selection
sandbox_plan_required_before_execution
status_pass
claim_boundary
```

Pass criteria:

- external install/import/runtime execution are false in M2600
- dependency mutation is false in M2600
- license/API review, source-build or adapter-probe review, and sandbox
  planning are represented as future prerequisites
- no dependency row implies platform selection, validation readiness, or result

## Validation-Role Compatibility Rows

M2600 should write validation-role compatibility rows:

```text
compatibility_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
platform_selection_criteria_materialized_in_m2600
reset_feasibility_evidence_required_later
rollout_feasibility_evidence_required_later
holdout_or_generalization_policy_required_later
external_validation_execution_allowed_in_m2600
validation_protocol_ready_in_m2600
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_platform_selection_compatibility`
- `stable_aes_aeb_infeasible_platform_selection_compatibility`

Pass criteria:

- exactly two HF3 low-cost pilot roles are represented
- both rows preserve P0 `72/3`
- reset feasibility, rollout feasibility, and holdout/generalization policy are
  future prerequisites, not M2600 execution
- external validation execution, validation protocol readiness, and validation
  result claims remain false

## Actor/Action Guard Rows

M2600 should write actor/action guard rows:

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
platform_selection_criteria_actor_visible
protocol_status_actor_visible
action_contract_mutation_detected
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist, one per validation-role compatibility row
- both rows preserve P0 observation shape `72` and action shape `3`
- hidden/oracle inputs, diagnostics, taxonomy labels, backend status, reset
  outcome, rollout outcome, validation outcome, platform selection,
  platform-selection criteria, and protocol status remain actor-invisible
- no action contract mutation is detected

## Claim-Boundary Rows

M2600 should write claim-boundary rows:

```text
claim_id
claim_family
claim_allowed_in_m2600
evidence_required_before_claim
status_pass
claim_boundary
```

The only allowed positive claim family is:

```text
after_closure_platform_selection_criteria_materialized
```

Forbidden claim families must include:

- `platform_selected_for_validation`
- `selection_decision_made`
- `validation_protocol_ready`
- `validation_admission_granted`
- `external_validation_execution`
- `high_fidelity_validation_readiness`
- `high_fidelity_validation_result`
- `hf4_discrepancy_result`
- `rollout_success`
- `success_rate_or_controller_family_verdict`
- `controller_ranking_or_winner_selection`
- `checkpoint_promotion`
- `driver_performance`
- `paper_level_evidence`
- `finite_window_vs_gru_result`
- `current_sim_verdict`
- `level3_self_identification`

Pass criteria:

- exactly one positive criteria-materialized claim is allowed
- every selection/readiness/result/execution/ranking/performance/paper/self-ID
  claim remains false
- criteria materialization cannot be interpreted as validation admission

## M2600 Gate Matrix

M2600 should write gate rows:

```text
gate_id
gate_family
status_pass
observed
expected
failure_type
claim_boundary
```

Required gates:

- `source_artifacts_exist`
- `m2596_after_closure_readiness_accepted`
- `platform_selection_criteria_rows_complete`
- `auditability_rows_pass`
- `dependency_import_risk_rows_pass`
- `validation_role_compatibility_rows_pass`
- `actor_action_guard_rows_pass`
- `claim_boundary_rows_pass`
- `actor_action_contract_preserved`
- `no_platform_selected_or_external_execution`
- `validation_readiness_and_result_forbidden`

Failure classification:

- missing or stale source evidence: `lineage_invalid`
- actor/action drift or actor-visible forbidden status: `contract_violation`
- criteria rows upgraded to selection/readiness/result claims:
  `objective_overfit`
- incomplete role coverage: `scenario_sampling_failure`
- claimed metrics without execution evidence: `metric_artifact`

## Follow-Up Rule

If M2600 materializes all rows and gates, route to a result audit:

```text
m2601-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-result-audit
```

If any M2600 gate fails, route to contract repair, artifact repair,
platform-schema repair, or branch synthesis. Do not route directly to actual
platform selection, validation protocol readiness, or validation execution from
M2599.

## Rejected Claims

M2599 rejects:

- actual platform selection
- selection decision
- external dependency installation or import
- external simulator execution
- reset execution
- policy action execution
- environment stepping
- rollout execution
- validation execution
- validation protocol readiness
- validation admission
- validation readiness or result
- HF4 discrepancy result
- success rate
- controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver performance
- paper-level evidence
- finite-window-vs-GRU result
- current-sim verdict
- high-fidelity validation result
- level3 self-identification
