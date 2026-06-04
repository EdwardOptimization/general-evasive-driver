# M2603 Engineering Controller Route A Baseline HF3 After-Closure Platform Selection Decision Design

- status: completed
- decision: `route_to_hf3_after_closure_platform_selection_decision_materialization_preflight`
- manifest: `experiments/manifests/m2603-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-design.json`
- parent synthesis: `docs/m2602-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-result-synthesis.md`
- parent audit: `docs/m2601-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-criteria-materialization-result-audit.md`
- parent materialization summary: `runs/m2600_engineering_controller_route_a_hf3_after_closure_platform_selection_criteria/summary.json`
- follow-up manifest: `experiments/manifests/m2604-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-preflight.json`
- next: `m2604-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-preflight`

## Design Verdict

M2603 designs the bounded after-closure HF3 platform-selection decision
artifacts required before a future platform-selection decision can be proposed.
M2604 should materialize decision-request, evidence-admission,
candidate-comparison, dependency/install/import guard, validation-role
compatibility, actor/action guard, claim-boundary, and gate rows.

This design is intentionally still not a selection result. It does not select a
platform, make a selection decision, install or import external simulator
dependencies, run high-fidelity simulation, execute resets, execute policy
actions, step environments, execute rollouts, execute validation, train, rank
controllers, promote checkpoints, compute success rates, or claim driver
performance.

If M2604 passes all gates, the allowed claim is limited to after-closure
platform-selection decision design artifacts materialized. That would still not
imply actual platform selection, validation protocol readiness, validation
admission, high-fidelity validation readiness, validation result, HF4
discrepancy result, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, level3 self-ID, or professional driver behavior.

## Source Evidence

Accepted criteria boundary:

```text
M2602 synthesis decision: continue_to_hf3_after_closure_platform_selection_decision_design
M2601 audit decision: accept_hf3_after_closure_platform_selection_criteria_materialization_route_to_result_synthesis
M2600 status_pass: true
platform-selection criteria rows: 3/3 pass
auditability rows: 3/3 pass
dependency/import risk rows: 3/3 pass
validation-role compatibility rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 18/18 pass
materialization gates: 11/11 pass
platform_selection_criteria_materialized_in_m2600: true
platform_selected_in_m2600: false
selection_decision_allowed_in_m2600: false
validation_protocol_ready_in_m2600: false
external_validation_execution_allowed_in_m2600: false
driver_performance_claim_allowed_in_m2600: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, prefer an
open/auditable high-fidelity vehicle dynamics layer, keep black-box simulators
demonstration-only, and keep repo-local current-sim diagnostic-only.

## M2604 Artifact Contract

M2604 should write:

```text
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/summary.json
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_request_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_evidence_admission_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_candidate_comparison_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_dependency_guard_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_validation_role_compatibility_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_actor_action_guard_rows.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/hf3_after_closure_platform_selection_decision_claim_boundary_checks.csv
runs/m2604_engineering_controller_route_a_hf3_after_closure_platform_selection_decision/after_closure_platform_selection_decision_gate_matrix.csv
docs/m2604-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-preflight.md
```

Every M2604 row should prove decision-design materialization only. Rows must
keep:

```text
platform_selection_decision_design_materialized_in_m2604: true
platform_selected_in_m2604: false
selection_decision_made_in_m2604: false
selected_platform_family_in_m2604: none
validation_protocol_ready_in_m2604: false
validation_admission_granted_in_m2604: false
external_validation_execution_allowed_in_m2604: false
driver_performance_claim_allowed_in_m2604: false
```

## Decision-Request Rows

M2604 should write decision-request rows:

```text
decision_request_id
decision_scope
criteria_materialization_accepted_before_request
actual_selection_allowed_in_m2604
selection_decision_made_in_m2604
selected_platform_family_in_m2604
future_selection_requires_result_audit
future_protocol_readiness_required_after_selection
status_pass
claim_boundary
```

Required rows:

- `preferred_open_auditable_backend_decision_request`
- `demonstration_and_diagnostic_exclusion_request`

Pass criteria:

- decision-design can be represented as future request preparation
- no row selects a platform
- no row makes a selection decision
- no row allows validation readiness or result interpretation

## Evidence-Admission Rows

M2604 should write evidence-admission rows:

```text
evidence_admission_id
source_artifact
evidence_role
admitted_for_decision_design_in_m2604
admitted_for_actual_selection_in_m2604
admitted_for_validation_readiness_in_m2604
status_pass
claim_boundary
```

Required evidence roles:

- `criteria_materialization_summary`
- `criteria_rows`
- `auditability_rows`
- `dependency_import_risk_rows`
- `validation_role_compatibility_rows`
- `actor_action_guard_rows`
- `claim_boundary_rows`
- `criteria_gate_matrix`

Pass criteria:

- M2600/M2601/M2602 evidence is admitted for decision design only
- actual selection and validation readiness remain false
- missing source artifacts fail as `lineage_invalid`

## Candidate-Comparison Rows

M2604 should write candidate-comparison rows:

```text
candidate_comparison_id
platform_family
comparison_role
open_auditable_backend_preferred
source_or_equivalent_trace_required
black_box_demonstration_only
repo_local_diagnostic_only
eligible_for_future_selection_after_audit
selected_in_m2604
status_pass
claim_boundary
```

Required platform families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- open/equivalent backend is preferred for future selection only
- black-box backend remains demonstration-only
- repo-local current-sim remains diagnostic-only
- no candidate is selected in M2604

## Dependency/Install/Import Guard Rows

M2604 should write dependency guard rows:

```text
dependency_guard_id
platform_family
external_install_allowed_in_m2604
external_import_allowed_in_m2604
runtime_execution_allowed_in_m2604
dependency_mutation_allowed_in_m2604
license_or_api_review_required_before_install
source_build_or_adapter_probe_required_before_selection
sandbox_plan_required_before_execution
status_pass
claim_boundary
```

Pass criteria:

- external install/import/runtime execution are false in M2604
- dependency mutation is false in M2604
- future review prerequisites remain represented
- no dependency row implies selection, readiness, or result

## Validation-Role Compatibility Rows

M2604 should write validation-role compatibility rows:

```text
compatibility_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
decision_design_materialized_in_m2604
reset_feasibility_evidence_required_later
rollout_feasibility_evidence_required_later
holdout_or_generalization_policy_required_later
external_validation_execution_allowed_in_m2604
validation_protocol_ready_in_m2604
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_platform_selection_decision_compatibility`
- `stable_aes_aeb_infeasible_platform_selection_decision_compatibility`

Pass criteria:

- exactly two HF3 low-cost pilot roles are represented
- both rows preserve P0 `72/3`
- reset feasibility, rollout feasibility, and holdout/generalization policy are
  future prerequisites, not M2604 execution
- external validation execution, validation protocol readiness, and validation
  result claims remain false

## Actor/Action Guard Rows

M2604 should write actor/action guard rows:

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
platform_selection_decision_actor_visible
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
  platform-selection criteria, platform-selection decision, and protocol status
  remain actor-invisible
- no action contract mutation is detected

## Claim-Boundary Rows

M2604 should write claim-boundary rows:

```text
claim_id
claim_family
claim_allowed_in_m2604
evidence_required_before_claim
status_pass
claim_boundary
```

The only allowed positive claim family is:

```text
after_closure_platform_selection_decision_design_materialized
```

Forbidden claim families must include:

- `platform_selected_for_validation`
- `selection_decision_made`
- `selected_platform_family`
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

- exactly one positive decision-design-materialized claim is allowed
- every selection/readiness/result/execution/ranking/performance/paper/self-ID
  claim remains false
- decision-design materialization cannot be interpreted as actual selection

## M2604 Gate Matrix

M2604 should write gate rows:

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
- `m2600_m2601_m2602_criteria_evidence_accepted`
- `decision_request_rows_complete`
- `evidence_admission_rows_pass`
- `candidate_comparison_rows_pass`
- `dependency_guard_rows_pass`
- `validation_role_compatibility_rows_pass`
- `actor_action_guard_rows_pass`
- `claim_boundary_rows_pass`
- `actor_action_contract_preserved`
- `no_platform_selected_or_external_execution`
- `validation_readiness_and_result_forbidden`

Failure classification:

- missing or stale source evidence: `lineage_invalid`
- actor/action drift or actor-visible forbidden status: `contract_violation`
- decision rows upgraded to actual selection/readiness/result claims:
  `objective_overfit`
- incomplete role coverage: `scenario_sampling_failure`
- claimed metrics without execution evidence: `metric_artifact`

## Follow-Up Rule

If M2604 materializes all rows and gates, route to a result audit:

```text
m2605-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-materialization-result-audit
```

If any M2604 gate fails, route to contract repair, artifact repair,
platform-schema repair, or branch synthesis. Do not route directly to actual
platform selection, validation protocol readiness, or validation execution from
M2603.

## Rejected Claims

M2603 rejects:

- actual platform selection
- selection decision
- selected platform family
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
