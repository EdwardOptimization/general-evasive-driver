# m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260605T030240Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: route_to_post_negative_diagnostic_source_diverse_failure_taxonomy_result_audit
- Decision reason: M2740 materialization pass wrote 61 taxonomy rows from 18 execution rows 31 negative-context guard rows and 12 blocked guard rows with 3 diagnostic success context 1 collision 14 offtrack 11 protected-or-HF3 blockers 2 source-family context rows 2 task-family context rows 3 guardrail context rows 11 actor rows 33 claim rows and 23 gates all pass no reset policy action rollout validation training ranking performance paper current-sim high-fidelity full ideal driver or self-ID claim routes to M2741 result audit

## Hypothesis

A no-rollout taxonomy materialization can turn M2737 source-diverse diagnostic rows into an auditable failure surface without ranking families or overclaiming performance.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
- parent_dataset: docs/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.md, docs/m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.md, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/summary.json, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/source_family_aggregate.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/task_family_aggregate.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/negative_context_guard_rows.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/blocked_surface_guard_rows.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/actor_contract_guard_rows.csv, runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/gate_matrix.csv, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.json, experiments/manifests/m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.json, experiments/manifests/m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight.json
- parent_objective: materialize no-rollout row-level failure taxonomy from M2737 source-diverse diagnostic execution after M2739 synthesis selects taxonomy before another execution
- derived_from: m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis, m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit, m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight
- blocked_by: M2737 diagnostic execution is complete but offtrack-dominated with 14/18 offtrack rows and 1/18 collision row, M2737 source-family and task-family aggregates are non-ranking and cannot select a winner, M2728 negative context protected blockers and HF3 blockers remain guardrails outside execution and denominators, another immediate M2737-like execution would repeat the same public diagnostic surface without taxonomy
- supersedes: direct source-family or task-family ranking from M2737 aggregates, another immediate source-diverse bounded execution before taxonomy, direct repair performance validation paper current-sim high-fidelity full-driver or self-ID interpretation from M2737
- invalidates: None

## Success Criteria

- runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json exists
- docs/m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight.md exists
- taxonomy artifacts account for 18 M2737 execution rows 31 negative-context guard rows and 12 blocked guard rows
- off_track collision_failure diagnostic_success_context negative_context_guard blocked_guard and protected_or_hf3_blocker rows remain separate
- source family task family and profile context remains diagnostic and non-ranking
- actor 72/action 3 no hidden/oracle actor input actor-invisible labels and protected rows outside denominators are preserved
- one result-audit follow-up manifest is registered

## Failure Criteria

- M2740 executes reset step policy action rollout replay validation training PPO source build adapter probe external simulation or private holdout
- M2740 changes actor input or action contract
- M2740 exposes taxonomy labels target labels protected labels source-family labels task-family labels blocker labels route labels success labels or verdicts to actor input
- M2740 drops success offtrack collision negative-context guard blocked guard protected blocker or HF3 blocker rows
- M2740 treats source-family task-family or profile aggregates as ranking winner selection promotion or success-rate verdict evidence
- M2740 treats negative context protected or HF3 rows as execution rows or ordinary denominators
- M2740 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result
- M2740 fails to register a bounded result-audit follow-up

## Evidence Gates

- M2740 must consume M2739 synthesis M2738 audit M2737 summary execution aggregate guard actor and gate artifacts before writing taxonomy
- M2740 must not execute reset step policy action rollout replay validation training PPO source build adapter probe external simulation private holdout or profile-specific tuning
- M2740 must classify all 18 M2737 execution rows while preserving 14 offtrack rows 1 collision row and 3 diagnostic success context rows
- M2740 must preserve 31 M2728 negative-context guard rows and 12 blocked guard rows as non-executed actor-invisible guardrails outside denominators
- M2740 must keep source-family task-family and profile context diagnostic and non-ranking
- M2740 must preserve P0 observation shape 72 action shape 3 no hidden/oracle actor input actor-invisible labels and protected rows outside denominators
- M2740 must write source accounting taxonomy aggregate source/task context guardrail context actor-contract claim-boundary gate summary and doc artifacts
- M2740 must register one result-audit follow-up before any repair design execution extension ranking validation or performance claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not execute reset
- do not step environments
- do not execute policy action
- do not execute policy rollout
- do not execute replay
- do not execute measured validation
- do not train
- do not run PPO
- do not execute source build
- do not execute adapter probe
- do not execute external simulation
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not expose taxonomy labels target labels off-track labels collision labels protected labels source-family labels task-family labels profile labels blocker labels gate outcomes route decisions success labels progress labels or verdict labels to actor input
- do not hide M2737 offtrack or collision rows
- do not hide M2737 diagnostic success context rows
- do not hide M2728 negative context rows
- do not hide protected blocker or HF3 blocker rows
- do not treat protected mitigation rows or HF3 source dependency blocker rows as ordinary success denominators
- do not rank controller families source families profiles or task families
- do not select a winner
- do not compute success-rate or controller-family verdict metrics
- do not claim repair success
- do not claim validation readiness
- do not claim validation result
- do not claim high-fidelity validation readiness
- do not claim high-fidelity validation result
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim current-sim verdict
- do not claim level3 self-identification
- do not claim driver performance from M2740 taxonomy materialization

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout

## Scoreboard

- milestone: m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight
- type: infrastructure
- checkpoint: runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_post_negative_diagnostic_source_diverse_failure_taxonomy_result_audit
- reason: M2740 materialization pass wrote 61 taxonomy rows from 18 execution rows 31 negative-context guard rows and 12 blocked guard rows with 3 diagnostic success context 1 collision 14 offtrack 11 protected-or-HF3 blockers 2 source-family context rows 2 task-family context rows 3 guardrail context rows 11 actor rows 33 claim rows and 23 gates all pass no reset policy action rollout validation training ranking performance paper current-sim high-fidelity full ideal driver or self-ID claim routes to M2741 result audit

## Next Blocker

post-negative diagnostic source-diverse failure taxonomy result audit
