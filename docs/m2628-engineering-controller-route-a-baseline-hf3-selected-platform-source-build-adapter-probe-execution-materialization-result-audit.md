# M2628 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Materialization Result Audit

- status: completed
- decision: `accept_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_route_to_result_synthesis`
- manifest: `experiments/manifests/m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-audit.json`
- parent summary: `runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json`
- parent doc: `docs/m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis.json`
- next: `m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis`

## Audit Verdict

M2628 accepts M2627 as Route A HF3 selected-platform
source-build/adapter-probe execution design materialization evidence. The
accepted claim remains bounded: M2627 materialized static source-build command
contract, adapter-probe command contract, dependency/environment isolation
guard, source-build artifact capture, adapter-probe trace capture,
source-build/adapter-probe outcome taxonomy, actor/action guard,
claim-boundary, and gate rows for
`chrono_vehicle_or_equivalent_open_backend`.

M2628 does not accept dependency execution readiness, source-build execution,
adapter-probe execution, backend availability, reset execution, reset success,
step execution, policy action execution, rollout execution, replay execution,
rollout feasibility, validation protocol readiness, validation admission,
high-fidelity validation readiness, validation result, external validation
execution, driver-performance claim, controller ranking, checkpoint promotion,
success rate, paper evidence, finite-window-vs-GRU result, current-sim verdict,
or level3 self-identification claim.

## Evidence Checks

Accepted M2627 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_preflight_pass
source_artifacts_exist: true
missing_source_artifacts: []
source_build_command_contract_row_count: 2
adapter_probe_command_contract_row_count: 2
dependency_environment_isolation_guard_row_count: 4
source_build_artifact_capture_row_count: 4
adapter_probe_trace_capture_row_count: 4
outcome_taxonomy_row_count: 10
actor_action_guard_row_count: 2
claim_boundary_check_count: 28
materialization_gate_count: 13
materialization_gates_all_pass: true
selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627: true
selected_platform_family_in_m2627: chrono_vehicle_or_equivalent_open_backend
forbidden_claim_allowed_in_m2627: false
external_install_allowed_in_m2627: false
external_import_allowed_in_m2627: false
runtime_execution_allowed_in_m2627: false
dependency_mutation_allowed_in_m2627: false
source_tree_mutation_allowed_in_m2627: false
network_access_allowed_in_m2627: false
source_build_executed_in_m2627: false
adapter_probe_executed_in_m2627: false
backend_started_in_m2627: false
reset_executed_in_m2627: false
environment_step_executed_in_m2627: false
policy_action_executed_in_m2627: false
rollout_executed_in_m2627: false
replay_executed_in_m2627: false
external_validation_execution_allowed_in_m2627: false
validation_protocol_ready_in_m2627: false
validation_admission_granted_in_m2627: false
validation_result_claim_allowed: false
backend_availability_claim_allowed_in_m2627: false
reset_success_claim_allowed_in_m2627: false
rollout_feasibility_claim_allowed_in_m2627: false
driver_performance_claim_allowed_in_m2627: false
observation_shape: 72
action_shape: 3
deployed_action_mapping: [steer, throttle, brake]
```

Required artifact audit:

```text
summary.json: present
hf3_selected_platform_source_build_command_contract_rows.csv: present
hf3_selected_platform_adapter_probe_command_contract_rows.csv: present
hf3_selected_platform_dependency_environment_isolation_guard_rows.csv: present
hf3_selected_platform_source_build_artifact_capture_rows.csv: present
hf3_selected_platform_adapter_probe_trace_capture_rows.csv: present
hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv: present
hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv: present
hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv: present
selected_platform_source_build_adapter_probe_execution_gate_matrix.csv: present
milestone doc: present
```

Row-count audit:

```text
source-build command contract rows: 2
adapter-probe command contract rows: 2
dependency/environment isolation guard rows: 4
source-build artifact capture rows: 4
adapter-probe trace capture rows: 4
source-build/adapter-probe outcome taxonomy rows: 10
actor/action guard rows: 2
claim-boundary rows: 28
gate rows: 13
```

Gate audit:

```text
source_artifacts_exist: pass
m2623_m2624_m2625_reset_execution_readiness_evidence_accepted: pass
source_build_command_contract_rows_pass: pass
adapter_probe_command_contract_rows_pass: pass
dependency_environment_isolation_guard_rows_pass: pass
source_build_artifact_capture_rows_pass: pass
adapter_probe_trace_capture_rows_pass: pass
outcome_taxonomy_rows_pass: pass
actor_action_guard_rows_pass: pass
claim_boundary_rows_pass: pass
no_install_import_mutation_build_probe_reset_step_action_rollout_replay_or_validation_execution: pass
source_build_adapter_probe_reset_validation_and_performance_forbidden: pass
actor_action_contract_preserved: pass
```

Source-build/adapter-probe design panel audit:

```text
selected platform: chrono_vehicle_or_equivalent_open_backend
source-build command contracts: configure and compile rows materialized, build execution false, network false
adapter-probe command contracts: import and backend-probe rows materialized, adapter probe false, backend start false, reset false
isolation guards: install/import/dependency mutation/source-tree mutation/network/external runtime all false
source-build artifact capture rows: future capture contracts only, source_build_executed false, artifact_observed false
adapter-probe trace capture rows: future trace contracts only, adapter_probe_executed false, backend_started false, trace_observed false
outcome taxonomy rows: 10 fields present, actor-visible false, schema only
install/import/runtime/mutation/source-tree/network/build/probe/backend/reset/step/action/rollout/replay/validation: false
backend availability/reset success/rollout feasibility/validation readiness/admission/result/performance: false
```

Actor/action audit:

```text
actor observation shape: 72
action shape: 3
deployed action mapping: [steer, throttle, brake]
hidden/oracle actor input detected: false
diagnostics actor visible: false
taxonomy labels actor visible: false
backend status actor visible: false
build outcome actor visible: false
probe outcome actor visible: false
reset outcome actor visible: false
rollout outcome actor visible: false
validation outcome actor visible: false
selected platform actor visible: false
protocol status actor visible: false
actor input mutation detected: false
action contract mutation detected: false
```

The selected-platform source-build/adapter-probe execution design rows are
accepted as workflow metadata for future synthesis and bounded execution
planning only. They are not source-build execution, adapter-probe execution,
backend availability, reset execution, reset success, rollout feasibility,
validation protocol readiness, validation admission, validation result, or
driver-performance evidence.

## Supported Claims

Supported:

- HF3 selected-platform source-build/adapter-probe execution design
  materialization artifacts are present for Route A
- the selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- source-build command contracts are materialized without source build
  execution, dependency mutation, or network access
- adapter-probe command contracts are materialized without adapter probe,
  backend start, or reset
- dependency/environment isolation guards keep install, import, source-tree
  mutation, dependency mutation, network access, and external runtime false
- source-build artifact capture rows and adapter-probe trace capture rows are
  future audit contracts only
- outcome taxonomy rows define future audit metadata while keeping outcome,
  status, and diagnostic fields actor-invisible
- actor/action guard rows preserve P0 `72/3`
- only static source-build/adapter-probe execution design materialization
  claims are allowed

## Rejected Claims

Not supported:

- dependency ready for execution
- source build executed
- adapter probe executed
- backend availability
- reset executed
- reset success
- environment step executed
- policy action executed
- rollout executed
- replay executed
- rollout feasibility
- validation protocol ready
- validation admission granted
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2627/M2628 are selected-platform source-build/adapter-probe execution design
materialization and audit only. They do not install, import, build, probe,
start a backend, reset, step, run a policy action, roll out, replay, validate,
compare controller families, or prove professional driver behavior.

## Failure Taxonomy

No M2627/M2628 failure is accepted for:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 validation-layer route.
- `objective_overfit`: source-build/adapter-probe execution design rows can be
  overclaimed if treated as source-build execution, adapter-probe execution,
  backend availability, reset execution, reset success, rollout feasibility,
  validation protocol readiness, validation admission, validation readiness,
  validation result, or performance evidence.
- `lineage_invalid`: not triggered here, but future execution still requires
  explicit source-build execution evidence, explicit adapter-probe execution
  evidence, backend availability evidence, reset invocation evidence, reset
  outcome audit, validation-admission evidence, and claim-boundary audit
  evidence.

## Next Route

Route to:

```text
m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis
```

M2629 should synthesize M2627/M2628 and decide whether the next bounded step is
selected-platform source-build/adapter-probe execution-attempt design, artifact
repair, contract repair, platform-schema repair, branch synthesis pivot, or
stop. It must not claim dependency execution readiness, source-build
execution, adapter-probe execution, backend availability, reset execution,
reset success, rollout feasibility, validation protocol readiness, validation
admission, validation readiness, validation result, driver performance,
ranking, paper evidence, or self-ID.
