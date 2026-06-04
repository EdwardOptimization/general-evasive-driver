# m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260604T053140Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_preflight_pass
- Decision reason: M2627 materializes selected-platform source-build/adapter-probe execution design artifacts status_pass true 2 source-build command rows 2 adapter-probe command rows 4 isolation guard rows 4 artifact capture rows 4 trace capture rows 10 outcome taxonomy rows 2 actor/action guard rows 28 claim rows and 13 gates pass no install import dependency mutation source build adapter probe backend start reset validation readiness/result ranking driver-performance paper FW-vs-GRU high-fidelity or self-ID claim

## Hypothesis

The Route A baseline can materialize bounded HF3 selected-platform source-build/adapter-probe execution design artifacts for chrono_vehicle_or_equivalent_open_backend while preserving the 72/3 no-oracle actor contract execution honesty and no external execution validation or performance claims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt, runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
- parent_dataset: docs/m2626-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-design.md, docs/m2625-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-synthesis.md, docs/m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-audit.md, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/summary.json, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_backend_availability_fixture_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_invocation_dry_run_contract_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_request_binding_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_actor_view_after_reset_extraction_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_outcome_audit_schema_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_actor_action_guard_rows.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_readiness_claim_boundary_checks.csv, runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/selected_platform_reset_execution_readiness_gate_matrix.csv, docs/post-m2470-route-plan.md, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2626-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-design.json, experiments/manifests/m2625-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-synthesis.json, experiments/manifests/m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-audit.json, experiments/manifests/m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-preflight.json
- parent_objective: materialize bounded selected-platform source-build/adapter-probe execution design artifacts after M2626 design
- derived_from: m2626-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-design, m2625-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-synthesis, m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-audit, m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-preflight
- blocked_by: M2626 designs source-build/adapter-probe execution materialization rows while rejecting dependency readiness source-build execution adapter-probe execution backend availability reset execution reset success validation readiness result and driver-performance claims, M2625 selects source-build/adapter-probe execution design after accepted selected-platform reset-execution readiness materialization evidence, Route C requires source-build/adapter-probe execution evidence contracts before any reset invocation rollout feasibility or external validation route can be interpreted
- supersedes: another selected-platform source-build/adapter-probe execution design-only milestone without materialization, executing source build adapter probe or reset directly from M2626 design, claiming source-build execution adapter-probe execution backend availability reset success rollout feasibility validation admission or validation readiness from design rows, starting external validation execution directly from M2626 design
- invalidates: None

## Success Criteria

- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_command_contract_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_command_contract_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_dependency_environment_isolation_guard_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_artifact_capture_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_trace_capture_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv exists
- runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/selected_platform_source_build_adapter_probe_execution_gate_matrix.csv exists
- docs/m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight.md exists
- selected-platform source-build/adapter-probe execution design rows keep external install import runtime execution dependency mutation source-tree mutation network access source build adapter probe backend start reset step action rollout replay validation false
- actor/action rows preserve P0 72/3 and keep metadata/outcomes/statuses actor-invisible
- claim-boundary rows keep dependency execution readiness source-build execution adapter-probe execution backend availability reset execution reset success validation protocol readiness validation admission validation readiness/result external execution ranking driver-performance paper self-ID finite-window-vs-GRU current-sim and high-fidelity validation verdict claims false
- no external high-fidelity simulation install import execution source build adapter probe backend start reset policy action training replay PPO ranking winner success-rate promotion validation admission readiness result or verdict claim is made

## Failure Criteria

- M2627 installs imports or runs Chrono or another external simulator
- M2627 changes actor input or action contract
- M2627 injects hidden or oracle actor features
- M2627 exposes labels feasibility classes backend statuses diagnostics build outcomes probe outcomes reset outcomes rollout outcomes validation outcomes platform selection platform-selection criteria platform-selection decision selected platform or protocol status to actor input
- M2627 silently upgrades source-build/adapter-probe execution design rows to source-build executed adapter-probe executed backend-available reset-executed reset-success validation-admitted validation-ready or validation-result rows
- M2627 mutates dependencies or source trees executes source build adapter probe backend start reset policy rollout step replay validation or interprets materialization artifacts as performance
- M2627 starts training
- M2627 ranks controller families or selects a controller winner
- M2627 computes success rate or promotes a checkpoint
- M2627 claims dependency execution readiness source-build execution adapter-probe execution backend availability reset execution reset success validation protocol readiness validation admission validation readiness result high-fidelity validation paper finite-window-vs-GRU current-sim verdict or self-ID result

## Evidence Gates

- M2627 must materialize summary source-build command contract adapter probe command contract dependency/environment isolation guard source-build artifact capture adapter-probe trace capture outcome taxonomy actor/action guard claim-boundary gate matrix and milestone doc artifacts
- M2627 must keep selected_platform_family chrono_vehicle_or_equivalent_open_backend and must not select black-box or repo-local current-sim as validation authority
- M2627 must distinguish selected-platform source-build/adapter-probe execution design materialization from dependency execution readiness source build execution adapter probe execution backend availability reset execution reset success rollout feasibility validation protocol readiness validation admission validation readiness validation result and driver-performance claims
- M2627 must preserve P0 observation shape 72 action shape 3 no hidden/oracle actor inputs and no rule-switching controller mode
- M2627 must keep taxonomy labels feasibility classes backend statuses diagnostics build/probe/reset/rollout/validation outcomes platform selection platform-selection criteria platform-selection decision selected platform and protocol status out of actor-visible inputs
- M2627 must not install import or run external high-fidelity simulation execute source build adapter probe backend start reset step policy action rollout replay validation train PPO rank controllers select winners promote checkpoints compute success rates or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not execute source build in the materialization preflight
- do not execute adapter probe in the materialization preflight
- do not start a backend in the materialization preflight
- do not mutate selected-platform dependencies
- do not mutate selected-platform source trees
- do not use network access for dependency resolution
- do not execute reset in the materialization preflight
- do not execute policy actions in the materialization preflight
- do not step environments in the materialization preflight
- do not execute rollout in the materialization preflight
- do not execute replay in the materialization preflight
- do not execute validation in the materialization preflight
- do not train in the materialization preflight
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not expose taxonomy labels feasibility classes backend statuses diagnostics build outcomes probe outcomes reset outcomes rollout outcomes validation outcomes platform selection platform-selection criteria platform-selection decision selected platform or protocol status to actor input
- do not silently upgrade source-build/adapter-probe execution design rows to source-build executed adapter-probe executed backend-available reset-executed reset-success validation-admitted validation-ready or validation-result rows
- do not claim dependency execution readiness
- do not claim source build execution
- do not claim adapter probe execution
- do not claim backend availability
- do not claim reset execution
- do not claim reset success
- do not claim rollout feasibility
- do not claim validation protocol readiness
- do not claim validation admission
- do not answer HF4 discrepancy questions
- do not rank controller families
- do not select a controller winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim high-fidelity validation result
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim current-sim verdict
- do not claim level3 self-identification
- do not claim driver performance from selected-platform source-build/adapter-probe execution design materialization

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight
- type: infrastructure
- checkpoint: runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_preflight_pass
- reason: M2627 materializes selected-platform source-build/adapter-probe execution design artifacts status_pass true 2 source-build command rows 2 adapter-probe command rows 4 isolation guard rows 4 artifact capture rows 4 trace capture rows 10 outcome taxonomy rows 2 actor/action guard rows 28 claim rows and 13 gates pass no install import dependency mutation source build adapter probe backend start reset validation readiness/result ranking driver-performance paper FW-vs-GRU high-fidelity or self-ID claim

## Next Blocker

m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-audit
