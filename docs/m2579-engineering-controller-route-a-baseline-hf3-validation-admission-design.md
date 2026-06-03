# M2579 Engineering Controller Route A Baseline HF3 Validation-Admission Design

- status: completed
- decision: `route_to_hf3_validation_admission_materialization_preflight`
- manifest: `experiments/manifests/m2579-engineering-controller-route-a-baseline-hf3-validation-admission-design.json`
- parent synthesis: `docs/m2578-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-result-synthesis.md`
- parent audit: `docs/m2577-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-result-audit.md`
- parent materialization summary: `runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/summary.json`
- follow-up manifest: `experiments/manifests/m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight.json`
- next: `m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight`

## Design Verdict

M2579 designs the bounded artifacts required before Route A HF3 boundary
evidence can be considered for validation admission. The next milestone may
materialize validation-admission request, admission-criteria,
external-platform-readiness, evidence-sufficiency, actor/action guard,
claim-boundary, and gate rows.

M2579 does not grant validation admission. It does not claim validation
readiness, validation result, driver performance, rollout success, ranking,
paper evidence, current-sim verdict, finite-window-vs-GRU evidence, or
self-identification.

## Source Evidence

Accepted source boundary:

```text
M2578 synthesis decision: continue_to_hf3_validation_admission_design
M2577 audit decision: accept_hf3_validation_readiness_boundary_materialization_route_to_result_synthesis
M2576 status_pass: true
readiness request rows: 2
evidence admission rows: 12
platform boundary rows: 3
dependency policy rows: 3
scenario-discrepancy question rows: 8
actor-input isolation rows: 2
claim-boundary checks: 12
materialization gates: 10/10 pass
actor contract: P0 observation 72 / action 3
allowed operational claim: validation-readiness boundary materialized
validation admission claim: false
validation execution claim: false
high-fidelity validation readiness/result claim: false
ranking/promotion/driver-performance/self-ID claim: false
external high-fidelity simulation install/import/run: false
```

## M2580 Artifact Contract

M2580 should write:

```text
runs/m2580_engineering_controller_route_a_hf3_validation_admission/summary.json
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_validation_admission_request_rows.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_admission_criteria_rows.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_external_platform_readiness_rows.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_evidence_sufficiency_rows.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_actor_action_guard_rows.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/hf3_claim_boundary_checks.csv
runs/m2580_engineering_controller_route_a_hf3_validation_admission/validation_admission_gate_matrix.csv
docs/m2580-engineering-controller-route-a-baseline-hf3-validation-admission-materialization-preflight.md
```

## Validation-Admission Request Rows

M2580 should write two request rows:

```text
admission_request_id
source_readiness_request_id
source_rollout_request_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
boundary_materialized
validation_admission_granted_in_m2580
validation_execution_allowed_in_m2580
external_simulation_allowed_in_m2580
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_validation_admission_request`
- `stable_aes_aeb_infeasible_validation_admission_request`

Pass criteria:

- exactly two rows exist
- both rows map to accepted M2576 readiness requests
- both rows preserve P0 `72/3`
- boundary materialized is true
- validation admission remains false in M2580
- validation execution and external simulation remain false in M2580

## Admission-Criteria Rows

M2580 should write criteria rows:

```text
admission_criteria_id
admission_request_id
criteria_family
criteria_description
criteria_satisfied_by_m2580
required_before_validation_admission
status_pass
claim_boundary
```

Required criteria families:

- `boundary_materialization_accepted`
- `actor_action_contract_preserved`
- `external_platform_ready`
- `validation_protocol_defined`
- `claim_boundary_audited`
- `holdout_or_generalization_policy_defined`

Pass criteria:

- boundary materialization and actor/action contract criteria may be true
- external-platform, validation-protocol, claim-boundary audit, and holdout or
  generalization criteria must remain required before validation admission
- no criteria row may grant validation readiness or result

## External-Platform Readiness Rows

M2580 should write platform readiness rows:

```text
external_platform_readiness_id
platform_family
open_auditable_backend_required
install_allowed_in_m2580
import_allowed_in_m2580
runtime_execution_allowed_in_m2580
platform_selected_in_m2580
status_pass
claim_boundary
```

Required platform families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- install/import/runtime execution are false in M2580
- no platform is selected in M2580
- the preferred future platform remains open and auditable
- black-box industry backends remain optional demonstration only

## Evidence-Sufficiency Rows

M2580 should write evidence-sufficiency rows:

```text
evidence_sufficiency_id
evidence_family
available_in_m2580
missing_before_validation_admission
missing_before_validation_readiness
missing_before_validation_result
status_pass
claim_boundary
```

Required evidence families:

- `m2576_boundary_materialization`
- `m2577_boundary_audit`
- `m2578_boundary_synthesis`
- `external_platform_selection`
- `validation_protocol`
- `validation_execution_result`
- `claim_boundary_audit_after_admission`

Pass criteria:

- M2576/M2577/M2578 evidence may be available
- external platform selection, validation protocol, validation execution result,
  and post-admission claim-boundary audit remain missing
- validation readiness and validation result remain false

## Actor/Action Guard Rows

M2580 should write actor/action guard rows:

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
action_contract_mutation_detected
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- hidden/oracle, diagnostics, labels, backend status, reset outcome, rollout
  outcome, and validation outcome are false
- action contract mutation is false

## Claim Boundary Checks

M2580 should write claim-boundary rows for:

- validation-admission design materialized
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

Only the operational claim `validation-admission design materialized` may become
true after M2580 if all design materialization rows pass. Validation admission,
validation readiness/result, external execution, HF4 discrepancy result, rollout
success, ranking, promotion, success rate, driver performance, paper evidence,
and self-ID remain false.

## Gate Matrix

M2580 should pass only if:

```text
source_artifacts_exist
validation_admission_request_rows_complete
admission_criteria_rows_pass
external_platform_readiness_rows_pass
evidence_sufficiency_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, actor input mutation, action contract mutation, reset execution,
policy action, environment step, rollout execution, validation execution,
training, replay, PPO, ranking, winner selection, checkpoint promotion,
success-rate computation, validation admission claim, validation readiness
claim, validation result claim, rollout success claim, driver-performance claim,
paper claim, finite-window-vs-GRU claim, current-sim verdict claim,
high-fidelity validation claim, HF4 discrepancy result claim, and self-ID claim.

## Follow-Up

Route to M2580 validation-admission materialization preflight. M2580 should
materialize static admission design artifacts only. If M2580 passes, the next
task should audit the admission design materialization before any external
validation-readiness or validation-execution design is selected.
