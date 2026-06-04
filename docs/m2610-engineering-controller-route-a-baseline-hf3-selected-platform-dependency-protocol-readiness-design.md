# M2610 Engineering Controller Route A Baseline HF3 Selected-Platform Dependency/Protocol Readiness Design

- status: completed
- decision: `route_to_hf3_selected_platform_dependency_protocol_readiness_materialization_preflight`
- manifest: `experiments/manifests/m2610-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-design.json`
- parent synthesis: `docs/m2609-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-result-materialization-result-synthesis.md`
- parent audit: `docs/m2608-engineering-controller-route-a-baseline-hf3-after-closure-platform-selection-decision-result-materialization-result-audit.md`
- parent materialization summary: `runs/m2607_engineering_controller_route_a_hf3_after_closure_platform_selection_decision_result/summary.json`
- follow-up manifest: `experiments/manifests/m2611-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-preflight.json`
- next: `m2611-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-preflight`

## Design Verdict

M2610 designs the bounded artifacts required to represent selected-platform
dependency/protocol readiness for
`chrono_vehicle_or_equivalent_open_backend`. M2611 should materialize selected
platform dependency inventory, source/build/adapter probe readiness, protocol
skeleton, validation-admission prerequisite, actor/action guard,
claim-boundary, and gate rows.

This design is intentionally still pre-validation. It does not install or
import external simulation dependencies, mutate dependencies, run external
simulation, execute resets, execute policy actions, step environments, execute
rollouts, execute validation, train, rank controllers, promote checkpoints,
compute success rates, or claim driver performance.

If M2611 passes all gates, the allowed claim is limited to selected-platform
dependency/protocol readiness design artifacts materialized. That would still
not imply dependency readiness for execution, validation protocol readiness,
validation admission, high-fidelity validation readiness, validation result,
HF4 discrepancy result, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, level3 self-ID, or professional driver behavior.

## Source Evidence

Accepted selected-platform boundary:

```text
M2609 synthesis decision: continue_to_hf3_selected_platform_dependency_protocol_readiness_design
M2608 audit decision: accept_hf3_after_closure_platform_selection_decision_result_materialization_route_to_result_synthesis
M2607 status_pass: true
decision-result rows: 1/1 pass
decision evidence rows: 12/12 pass
candidate-disposition rows: 3/3 pass
dependency/execution guard rows: 3/3 pass
validation-admission guard rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 17/17 pass
materialization gates: 12/12 pass
selected_platform_family_in_m2607: chrono_vehicle_or_equivalent_open_backend
selected_platform_family_is_open_auditable: true
black_box_backend_selected_in_m2607: false
repo_local_current_sim_selected_in_m2607: false
validation_protocol_ready_in_m2607: false
validation_admission_granted_in_m2607: false
external_validation_execution_allowed_in_m2607: false
driver_performance_claim_allowed_in_m2607: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, prefer an
open/auditable high-fidelity vehicle dynamics layer, keep black-box simulators
demonstration-only, and keep repo-local current-sim diagnostic-only.

## M2611 Artifact Contract

M2611 should write:

```text
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/summary.json
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_dependency_inventory_rows.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_source_build_adapter_probe_readiness_rows.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_protocol_skeleton_rows.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_validation_admission_prerequisite_rows.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_actor_action_guard_rows.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/hf3_selected_platform_dependency_protocol_claim_boundary_checks.csv
runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/selected_platform_dependency_protocol_readiness_gate_matrix.csv
docs/m2611-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-preflight.md
```

Every M2611 row should prove selected-platform dependency/protocol readiness
design artifacts only. Rows must keep:

```text
selected_platform_dependency_protocol_readiness_design_materialized_in_m2611: true
selected_platform_family_in_m2611: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2611: false
external_import_allowed_in_m2611: false
runtime_execution_allowed_in_m2611: false
dependency_mutation_allowed_in_m2611: false
validation_protocol_ready_in_m2611: false
validation_admission_granted_in_m2611: false
external_validation_execution_allowed_in_m2611: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2611: false
```

## Selected-Platform Dependency Inventory Rows

M2611 should write dependency inventory rows:

```text
dependency_inventory_id
selected_platform_family
dependency_family
dependency_role
source_or_equivalent_trace_required
license_or_api_review_required_later
source_build_or_adapter_probe_required_later
external_install_allowed_in_m2611
external_import_allowed_in_m2611
runtime_execution_allowed_in_m2611
dependency_mutation_allowed_in_m2611
status_pass
claim_boundary
```

Required dependency families:

- `vehicle_dynamics_backend_source`
- `scenario_adapter_contract`
- `sensor_actor_interface_contract`
- `result_export_and_replay_contract`

Pass criteria:

- selected platform family is `chrono_vehicle_or_equivalent_open_backend`
- source/equivalent trace remains required
- license/API review remains future work
- source/build/adapter probe remains future work
- install/import/runtime execution are false in M2611
- dependency mutation is false in M2611
- no dependency row may imply validation readiness or result

## Source/Build/Adapter Probe Readiness Rows

M2611 should write source/build/adapter probe readiness rows:

```text
probe_readiness_id
selected_platform_family
probe_family
probe_scope
source_or_equivalent_trace_required
static_contract_defined_in_m2611
source_build_executed_in_m2611
adapter_probe_executed_in_m2611
external_install_allowed_in_m2611
external_import_allowed_in_m2611
runtime_execution_allowed_in_m2611
dependency_mutation_allowed_in_m2611
status_pass
claim_boundary
```

Required probe families:

- `source_tree_or_equivalent_trace_probe`
- `build_system_contract_probe`
- `state_action_adapter_contract_probe`
- `deterministic_replay_export_contract_probe`

Pass criteria:

- every probe is a static contract only
- source build and adapter probe execution are false in M2611
- external install/import/runtime execution and mutation are false
- no probe row may imply executable protocol readiness

## Protocol Skeleton Rows

M2611 should write protocol skeleton rows:

```text
protocol_skeleton_id
route_role_id
selected_platform_family
actor_observation_shape
action_shape
protocol_skeleton_defined_in_m2611
reset_contract_required_later
rollout_contract_required_later
holdout_or_generalization_policy_required_later
source_build_or_adapter_probe_required_later
reset_allowed_in_m2611
policy_action_allowed_in_m2611
environment_step_allowed_in_m2611
rollout_allowed_in_m2611
external_validation_execution_allowed_in_m2611
validation_protocol_ready_in_m2611
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_selected_platform_protocol_skeleton`
- `stable_aes_aeb_infeasible_selected_platform_protocol_skeleton`

Pass criteria:

- exactly two rows exist
- both rows preserve P0 `72/3`
- protocol skeleton is a static contract only
- reset/rollout/holdout/source-build prerequisites remain later work
- reset/action/step/rollout/external validation execution are false in M2611
- validation protocol readiness and result claims remain false

## Validation-Admission Prerequisite Rows

M2611 should write validation-admission prerequisite rows:

```text
validation_admission_prerequisite_id
route_role_id
selected_platform_family
actor_observation_shape
action_shape
dependency_inventory_materialized_in_m2611
protocol_skeleton_materialized_in_m2611
source_build_or_adapter_probe_required_later
reset_feasibility_evidence_required_later
rollout_feasibility_evidence_required_later
executable_protocol_required_later
holdout_or_generalization_policy_required_later
validation_protocol_ready_in_m2611
validation_admission_granted_in_m2611
external_validation_execution_allowed_in_m2611
validation_result_claim_allowed
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- dependency inventory and protocol skeleton materialization are true
- every validation prerequisite remains later work
- validation protocol readiness, validation admission, external validation
  execution, and validation result claims are false

## Actor/Action Guard Rows

M2611 should write actor/action guard rows:

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
selected_platform_actor_visible
protocol_status_actor_visible
action_contract_mutation_detected
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- hidden/oracle, diagnostics, labels, backend status, reset outcome, rollout
  outcome, validation outcome, platform selection, platform-selection
  criteria, platform-selection decision, selected platform, and protocol
  status are false for actor-visible inputs
- action contract mutation is false

## Claim Boundary Checks

M2611 should write claim-boundary rows for:

- selected-platform dependency/protocol readiness design materialized
- dependency inventory materialized
- protocol skeleton materialized
- dependency ready for execution
- source build or adapter probe executed
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

Only the operational claims
`selected_platform_dependency_protocol_readiness_design_materialized`,
`selected_platform_dependency_inventory_materialized`, and
`selected_platform_protocol_skeleton_materialized` may become true after M2611
if all design materialization rows pass. Dependency execution readiness,
source-build execution, validation protocol readiness, validation admission,
validation readiness/result, external execution, HF4 discrepancy result,
rollout success, ranking, promotion, success rate, driver performance, paper
evidence, and self-ID remain false.

## Gate Matrix

M2611 should write `selected_platform_dependency_protocol_readiness_gate_matrix.csv`
with gates for:

- source artifacts exist
- M2607/M2608/M2609 selected-platform evidence accepted
- dependency inventory rows pass
- source/build/adapter probe readiness rows pass
- protocol skeleton rows pass
- validation-admission prerequisite rows pass
- actor/action guard rows pass
- claim-boundary rows pass
- actor/action contract preserved
- no external install/import/runtime execution or dependency mutation
- no reset/action/step/rollout/validation execution
- validation readiness/result/performance claims forbidden

All gates must pass before M2611 can route to result audit. A pass still means
static readiness-design materialization only, not executable validation
readiness or driver performance.
