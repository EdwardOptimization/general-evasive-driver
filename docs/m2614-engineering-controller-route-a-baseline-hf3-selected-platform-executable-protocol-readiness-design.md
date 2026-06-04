# M2614 Engineering Controller Route A Baseline HF3 Selected-Platform Executable-Protocol Readiness Design

- status: completed
- decision: `route_to_hf3_selected_platform_executable_protocol_readiness_materialization_preflight`
- manifest: `experiments/manifests/m2614-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-design.json`
- parent synthesis: `docs/m2613-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-synthesis.md`
- parent audit: `docs/m2612-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2615-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-preflight.json`
- next: `m2615-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-preflight`

## Design Verdict

M2614 designs the bounded artifacts required to represent selected-platform
executable-protocol readiness for
`chrono_vehicle_or_equivalent_open_backend`. M2615 should materialize
source/dependency review admission, build/probe plan, reset/step API readiness,
P0 actor extractor parity, action mapping parity, scenario-role binding,
result export/replay readiness, validation-admission prerequisite,
actor/action guard, claim-boundary, and gate rows.

This design is intentionally still pre-execution. It does not install or import
external simulation dependencies, mutate dependencies, run source builds, run
adapter probes, execute resets, execute policy actions, step environments,
execute rollouts, execute validation, train, rank controllers, promote
checkpoints, compute success rates, or claim driver performance.

If M2615 passes all gates, the allowed claim is limited to selected-platform
executable-protocol readiness design artifacts materialized. That would still
not imply dependency readiness for execution, validation protocol readiness,
validation admission, high-fidelity validation readiness, validation result,
HF4 discrepancy result, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, level3 self-ID, or professional driver behavior.

## Source Evidence

Accepted selected-platform dependency/protocol boundary:

```text
M2613 synthesis decision: continue_to_hf3_selected_platform_executable_protocol_readiness_design
M2612 audit decision: accept_hf3_selected_platform_dependency_protocol_readiness_materialization_route_to_result_synthesis
M2611 status_pass: true
dependency inventory rows: 4/4 pass
source/build/adapter probe readiness rows: 4/4 pass
protocol skeleton rows: 2/2 pass
validation-admission prerequisite rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 20/20 pass
materialization gates: 12/12 pass
selected_platform_family_in_m2611: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2611: false
external_import_allowed_in_m2611: false
runtime_execution_allowed_in_m2611: false
dependency_mutation_allowed_in_m2611: false
source_build_executed_in_m2611: false
adapter_probe_executed_in_m2611: false
reset_allowed_in_m2611: false
policy_action_allowed_in_m2611: false
environment_step_allowed_in_m2611: false
rollout_allowed_in_m2611: false
external_validation_execution_allowed_in_m2611: false
validation_protocol_ready_in_m2611: false
validation_admission_granted_in_m2611: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2611: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, prefer an
open/auditable high-fidelity vehicle dynamics layer, keep black-box simulators
demonstration-only, and keep repo-local current-sim diagnostic-only.

## M2615 Artifact Contract

M2615 should write:

```text
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/summary.json
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_source_dependency_review_admission_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_build_probe_plan_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_reset_step_api_readiness_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_actor_extractor_parity_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_action_mapping_parity_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_scenario_role_binding_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_result_export_replay_readiness_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_executable_protocol_validation_admission_prerequisite_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_executable_protocol_actor_action_guard_rows.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/hf3_selected_platform_executable_protocol_claim_boundary_checks.csv
runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/selected_platform_executable_protocol_readiness_gate_matrix.csv
docs/m2615-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-preflight.md
```

Every M2615 row should prove selected-platform executable-protocol readiness
design artifacts only. Rows must keep:

```text
selected_platform_executable_protocol_readiness_design_materialized_in_m2615: true
selected_platform_family_in_m2615: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2615: false
external_import_allowed_in_m2615: false
runtime_execution_allowed_in_m2615: false
dependency_mutation_allowed_in_m2615: false
source_build_executed_in_m2615: false
adapter_probe_executed_in_m2615: false
reset_executed_in_m2615: false
environment_step_executed_in_m2615: false
policy_action_executed_in_m2615: false
rollout_executed_in_m2615: false
external_validation_execution_allowed_in_m2615: false
validation_protocol_ready_in_m2615: false
validation_admission_granted_in_m2615: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2615: false
```

## Source/Dependency Review Admission Rows

M2615 should write source/dependency review admission rows:

```text
source_dependency_review_admission_id
selected_platform_family
review_family
review_scope
source_or_equivalent_trace_required
review_materialized_in_m2615
license_or_api_review_required_later
sandbox_plan_required_before_execution
external_install_allowed_in_m2615
external_import_allowed_in_m2615
runtime_execution_allowed_in_m2615
dependency_mutation_allowed_in_m2615
status_pass
claim_boundary
```

Required review families:

- `selected_platform_source_trace_admission`
- `dependency_license_api_review_admission`
- `execution_sandbox_plan_admission`
- `repo_local_adapter_boundary_admission`

Pass criteria:

- selected platform family is `chrono_vehicle_or_equivalent_open_backend`
- source/equivalent trace and review rows are materialized
- license/API review and sandbox plan remain future prerequisites
- install/import/runtime execution and dependency mutation are false in M2615
- no review row may imply dependency execution readiness

## Build/Probe Plan Rows

M2615 should write build/probe plan rows:

```text
build_probe_plan_id
selected_platform_family
plan_family
plan_scope
plan_materialized_in_m2615
source_build_required_later
adapter_probe_required_later
source_build_executed_in_m2615
adapter_probe_executed_in_m2615
external_install_allowed_in_m2615
external_import_allowed_in_m2615
runtime_execution_allowed_in_m2615
dependency_mutation_allowed_in_m2615
status_pass
claim_boundary
```

Required plan families:

- `source_build_plan`
- `state_action_adapter_probe_plan`
- `deterministic_replay_export_probe_plan`
- `failure_status_taxonomy_probe_plan`

Pass criteria:

- every plan is a static contract only
- source build and adapter probe execution are false in M2615
- external install/import/runtime execution and mutation are false
- no plan row may imply executable validation readiness

## Reset/Step API Readiness Rows

M2615 should write reset/step API readiness rows:

```text
reset_step_api_readiness_id
route_role_id
selected_platform_family
actor_observation_shape
action_shape
reset_api_contract_defined_in_m2615
step_api_contract_defined_in_m2615
termination_status_contract_defined_in_m2615
reset_executed_in_m2615
environment_step_executed_in_m2615
policy_action_executed_in_m2615
rollout_executed_in_m2615
external_validation_execution_allowed_in_m2615
validation_protocol_ready_in_m2615
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_step_api_readiness`
- `stable_aes_aeb_infeasible_reset_step_api_readiness`

Pass criteria:

- exactly two rows exist
- both rows preserve P0 `72/3`
- reset, step, and termination/status contracts are static contracts only
- reset/step/action/rollout/external validation execution are false in M2615
- validation protocol readiness and result claims remain false

## Actor Extractor Parity Rows

M2615 should write P0 actor extractor parity rows:

```text
actor_extractor_parity_id
route_role_id
selected_platform_family
actor_observation_shape
extractor_contract_defined_in_m2615
ego_kinematics_included
actuator_state_included
previous_command_included
road_geometry_included
obstacle_geometry_included
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
selected_platform_actor_visible
protocol_status_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- both rows preserve observation shape `72`
- actor-visible features are limited to deployable P0 information
- hidden/oracle, diagnostics, labels, backend status, selected platform, and
  protocol status are false

## Action Mapping Parity Rows

M2615 should write action mapping parity rows:

```text
action_mapping_parity_id
route_role_id
selected_platform_family
action_shape
deployed_action_mapping
action_mapping_contract_defined_in_m2615
steer_command_channel_preserved
throttle_command_channel_preserved
brake_command_channel_preserved
action_contract_mutation_detected
policy_action_executed_in_m2615
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- action shape is `3`
- deployed action mapping is `[steer, throttle, brake]`
- action contract mutation and policy action execution are false

## Scenario-Role Binding Rows

M2615 should write scenario-role binding rows:

```text
scenario_role_binding_id
route_role_id
selected_platform_family
scenario_role_contract_defined_in_m2615
scenario_label_actor_visible
reset_feasibility_evidence_required_later
rollout_feasibility_evidence_required_later
holdout_or_generalization_policy_required_later
reset_executed_in_m2615
rollout_executed_in_m2615
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_scenario_role_binding`
- `stable_aes_aeb_infeasible_scenario_role_binding`

Pass criteria:

- role metadata is protocol metadata only, not actor-visible input
- reset feasibility, rollout feasibility, and holdout policy remain future
  prerequisites
- reset, rollout, and validation result claims are false

## Result Export/Replay Readiness Rows

M2615 should write result export/replay readiness rows:

```text
result_export_replay_readiness_id
selected_platform_family
export_replay_family
export_replay_scope
contract_defined_in_m2615
replay_execution_required_later
validation_execution_required_later
replay_executed_in_m2615
external_validation_execution_allowed_in_m2615
validation_result_claim_allowed
status_pass
claim_boundary
```

Required export/replay families:

- `deterministic_result_schema`
- `replay_seed_and_lineage_manifest`
- `artifact_export_index`

Pass criteria:

- every row is a static contract only
- replay execution and validation execution remain future work
- replay execution, external validation execution, and result claims are false

## Validation-Admission Prerequisite Rows

M2615 should write executable-protocol validation-admission prerequisite rows:

```text
validation_admission_prerequisite_id
route_role_id
selected_platform_family
source_dependency_review_materialized_in_m2615
build_probe_plan_materialized_in_m2615
reset_step_api_contract_materialized_in_m2615
actor_extractor_parity_materialized_in_m2615
action_mapping_parity_materialized_in_m2615
scenario_role_binding_materialized_in_m2615
result_export_replay_materialized_in_m2615
source_build_or_adapter_probe_required_later
reset_feasibility_evidence_required_later
rollout_feasibility_evidence_required_later
executable_protocol_required_later
holdout_or_generalization_policy_required_later
validation_protocol_ready_in_m2615
validation_admission_granted_in_m2615
external_validation_execution_allowed_in_m2615
validation_result_claim_allowed
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- all M2615 static design panels are materialized
- every execution/validation prerequisite remains later work
- validation protocol readiness, validation admission, external validation
  execution, and validation result claims are false

## Actor/Action Guard Rows

M2615 should write actor/action guard rows:

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

M2615 should write claim-boundary rows for:

- selected-platform executable-protocol readiness design materialized
- source/dependency review admission materialized
- build/probe plan materialized
- reset/step API contract materialized
- actor extractor and action mapping contracts materialized
- scenario-role binding materialized
- result export/replay readiness materialized
- dependency ready for execution
- source build executed
- adapter probe executed
- reset executed
- environment step executed
- rollout success
- validation protocol ready
- validation admission granted
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- HF4 discrepancy result
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

Only the operational materialization claims may become true after M2615 if all
design materialization rows pass. Dependency execution readiness, source-build
execution, adapter-probe execution, reset/step execution, validation protocol
readiness, validation admission, validation readiness/result, external
execution, HF4 discrepancy result, rollout success, ranking, promotion,
success rate, driver performance, paper evidence, and self-ID remain false.

## Gate Matrix

M2615 should write `selected_platform_executable_protocol_readiness_gate_matrix.csv`
with gates for:

- source artifacts exist
- M2611/M2612/M2613 dependency/protocol readiness evidence accepted
- source/dependency review admission rows pass
- build/probe plan rows pass
- reset/step API readiness rows pass
- actor extractor parity rows pass
- action mapping parity rows pass
- scenario-role binding rows pass
- result export/replay readiness rows pass
- validation-admission prerequisite rows pass
- actor/action guard rows pass
- claim-boundary rows pass
- no dependency mutation/source build/adapter probe/reset/step/action/rollout/validation execution
- validation readiness/result/performance claims forbidden

All gates must pass before M2615 can route to result audit. A pass still means
static executable-protocol-readiness design materialization only, not
dependency execution readiness, executable validation readiness, validation
admission, validation result, or driver performance.
