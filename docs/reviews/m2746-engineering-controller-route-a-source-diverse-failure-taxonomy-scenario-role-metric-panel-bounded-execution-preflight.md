# m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight Research Review

## Summary

- Generated at UTC: 20260605T040627Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: route_to_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_result_audit
- Decision reason: M2746 bounded execution preflight status_pass true resolved and executed 14/14 candidates split 7 M2693 7 M2716 with 0 failures 5 guardrail contexts 18 actor guards 34 claim rows and 21 gates all pass termination counts 1 obstacle_collision 9 off_track 3 speed_too_low 1 unset_or_completed diagnostic success 1 collision 1 guardrails not executed actor 72/action 3 no hidden oracle no ranking validation performance paper current-sim high-fidelity full ideal driver or self-ID claim routes to M2747 result audit

## Hypothesis

A bounded role-panel execution preflight can produce closed-loop diagnostic rows from the audited M2743 offtrack target surface while preserving actor and claim boundaries.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
- parent_dataset: docs/m2745-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-design.md, docs/m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit.md, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/summary.json, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/scenario_role_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/metric_contract_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/target_panel_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/guardrail_context_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/actor_contract_guard_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/claim_boundary_rows.csv, runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/gate_matrix.csv, runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json, runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/target_execution_rows.csv, runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/exact_execution_rows.csv, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2745-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-design.json, experiments/manifests/m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit.json, experiments/manifests/m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight.json
- parent_objective: execute a bounded actor-safe diagnostic preflight over the 14 audited M2743 offtrack target rows without executing guardrail rows or ranking outcomes
- derived_from: m2745-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-design, m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit, m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight
- blocked_by: M2745 admits only bounded diagnostic execution over the 14 offtrack target rows, collision caution diagnostic success negative-context blocked protected and HF3 rows remain non-executed guardrails, source-family task-family and profile context remains diagnostic and non-ranking, M2746 must register a separate result audit before interpretation
- supersedes: another static scenario-role metric panel materialization without execution-admission change, direct execution from M2743 target rows without candidate resolution, profile ranking or repair success interpretation from M2743 role rows
- invalidates: None

## Success Criteria

- runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/summary.json exists
- execution_candidate_rows execution_candidate_resolution_rows candidate_execution_rows candidate_execution_failure_rows guardrail_context_rows actor_contract_guard_rows claim_boundary_rows gate_matrix run_state and doc artifacts exist
- all 14 M2743 offtrack target rows are resolved or explicitly accounted by failure rows
- collision caution diagnostic success negative-context blocked protected and HF3 guardrails are not executed and remain outside success denominators
- actor 72/action 3 no hidden oracle and actor-invisible labels are preserved
- one follow-up result audit manifest is registered
- M2746 makes no training ranking validation performance paper current-sim high-fidelity full ideal driver or self-ID claim

## Failure Criteria

- M2746 executes guardrail rows
- M2746 changes actor inputs or action contract or exposes hidden/oracle actor labels
- M2746 ranks controller families source families profiles task families selects a winner promotes a checkpoint or claims driver performance
- M2746 hides failed rows or treats diagnostic execution as validation readiness

## Evidence Gates

- M2746 must consume M2745 design M2744 audit and M2743 role metric target guardrail actor claim and gate artifacts
- M2746 must materialize execution_candidate_rows and execution_candidate_resolution_rows before any reset or step
- M2746 must account for exactly 14 M2743 offtrack_containment_target rows as execution candidates
- M2746 must execute only resolved offtrack target rows and must not execute collision caution diagnostic success negative-context blocked protected or HF3 guardrail rows
- M2746 must write candidate_execution_rows candidate_execution_failure_rows guardrail_context_rows actor_contract_guard_rows claim_boundary_rows gate_matrix run_state summary and doc artifacts
- M2746 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible scenario-role metric target protected blocker route-decision success progress and verdict labels
- M2746 must keep source-family task-family and profile context diagnostic and non-ranking
- M2746 must not execute replay validation training PPO source build adapter probe external simulation ranking promotion success-rate verdict computation or driver-performance claims
- M2746 must register one result-audit follow-up manifest before any interpretation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not fetch external source
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not execute source build
- do not execute adapter probe
- do not start an external backend
- do not execute collision caution rows
- do not execute diagnostic success context rows
- do not execute negative-context guard rows
- do not execute blocked same-surface rows
- do not execute protected blocker rows
- do not execute HF3 blocker rows
- do not execute replay
- do not execute measured validation
- do not train
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not expose scenario-role labels metric labels target labels protected labels blocker labels gate outcomes route decisions success labels progress labels or verdict labels to actor input
- do not treat collision caution diagnostic success negative-context blocked protected or HF3 rows as ordinary success denominators
- do not rank controller families source families profiles or task families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim repair success
- do not claim validation readiness
- do not claim validation result
- do not claim high-fidelity validation readiness
- do not claim high-fidelity validation result
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim current-sim verdict
- do not claim level3 self-identification
- do not claim full ideal driver completion
- do not claim driver performance from M2746 diagnostic execution

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout

## Scoreboard

- milestone: m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight
- type: infrastructure
- checkpoint: runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_result_audit
- reason: M2746 bounded execution preflight status_pass true resolved and executed 14/14 candidates split 7 M2693 7 M2716 with 0 failures 5 guardrail contexts 18 actor guards 34 claim rows and 21 gates all pass termination counts 1 obstacle_collision 9 off_track 3 speed_too_low 1 unset_or_completed diagnostic success 1 collision 1 guardrails not executed actor 72/action 3 no hidden oracle no ranking validation performance paper current-sim high-fidelity full ideal driver or self-ID claim routes to M2747 result audit

## Next Blocker

source-diverse failure taxonomy scenario-role metric panel bounded execution preflight
