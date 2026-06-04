# m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260604T131339Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: route_to_protocol_materialization_result_audit
- Decision reason: M2671 materializes Route B comparison protocol pack status_pass true with 9 controller-family rows 5 task-family rows 15 fairness-gate rows 21 claim-boundary rows and 15 gate-matrix rows includes L2 current-tiled and L3 reset/truncated controls actor 72/action 3 no hidden oracle rejects execution ranking promotion success-rate driver-performance paper FW-vs-GRU current-sim high-fidelity full ideal driver and self-ID claims routes to M2672 result audit

## Hypothesis

A machine-auditable protocol pack can convert the M2670 Route B admission design into concrete controller-family task-family fairness gate and claim-boundary rows without prematurely running or ranking controllers.

## Lineage

- parent_checkpoint: runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt, runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/checkpoints/m2648_gap_targeted_actor_head_repair.pt, runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
- parent_dataset: docs/m2670-paper-route-history-vs-current-response-comparison-admission-design.md, docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md, docs/post-m2470-route-plan.md, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md, docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md, docs/m1199-paper-route-fair-comparison-pilot-run.md, docs/m1200-paper-route-fair-comparison-pilot-result-audit.md, docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md
- parent_config: experiments/manifests/m2670-paper-route-history-vs-current-response-comparison-admission-design.json, experiments/manifests/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.json
- parent_objective: materialize a machine-auditable Route B history-vs-current-response comparison protocol pack after M2670 admission design
- derived_from: m2670-paper-route-history-vs-current-response-comparison-admission-design, m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis, post-m2470-route-plan, self-id-go-no-go-paper-route-plan, paper-route-finite-window-vs-gru-plan
- blocked_by: the comparison matrix is admitted only as a design until controller-family task-family fairness claim-boundary and gate rows are materialized, historical public pilot evidence had L2 window-equivalence and L3 reset-semantics issues, paper-route execution must not start until protocol rows make current-tiled and reset/truncated controls auditable
- supersedes: direct M1199-style public pilot rerun without current-tiled L2 and corrected L3 reset/truncated controls, controller-family ranking from readiness artifacts or historical public pilot trends
- invalidates: None

## Success Criteria

- docs/m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight.md exists
- runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/summary.json exists
- controller_family_rows.csv includes L0-current L1-one-step L2-window-13 L2-window-25 L2-window-50 L2-window-100 L2-current-tiled L3-online-GRU and L3-reset-truncated-control
- task_family_rows.csv includes T1 reactive T2 delayed response T3 diagnostic warmup T4 same-current different-older-history and T5 terminal-boundary tasks
- fairness_gate_rows.csv blocks missing actor-boundary action-contract seed/budget eval/cost and reset/current-tiled enforcement requirements
- claim_boundary_rows.csv blocks driver-performance paper finite-window-vs-GRU current-sim high-fidelity full ideal driver and self-ID claims
- gate_matrix.csv passes all materialization gates
- no reset step rollout replay validation training PPO source build adapter probe external simulation ranking winner promotion success-rate driver-performance validation-readiness paper finite-window-vs-GRU current-sim high-fidelity full ideal driver completion or self-ID claim is made

## Failure Criteria

- M2671 executes reset step rollout replay validation training PPO source build adapter probe or external simulation
- M2671 changes actor input or action contract
- M2671 exposes hidden dynamics oracle labels slip tire force TTC reference trajectory path error heading error required clearance controller labels collision success progress or precomputed answers to actor input
- M2671 ranks controller families selects a winner promotes a checkpoint or computes success-rate verdicts
- M2671 claims driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result
- M2671 fails to materialize all required controller-family task-family fairness gate and claim-boundary rows

## Evidence Gates

- M2671 must materialize controller-family rows for L0-current L1-one-step L2-window-13 L2-window-25 L2-window-50 L2-window-100 L2-current-tiled L3-online-GRU and L3-reset-truncated-control
- M2671 must materialize task-family rows for T1 reactive emergency avoidance T2 delayed actuator/response feedback T3 diagnostic warmup plus obstacle reveal T4 same-current same-recent-window different-older-history and T5 terminal-boundary near-constraint avoidance
- M2671 must materialize fairness gate rows covering same actor boundary same action contract same train/eval split same public gates no private holdout tuning parameter count observation dimension recurrent state dimension inference latency and runtime reporting
- M2671 must materialize claim-boundary rows that keep public pilot trends separate from driver-performance paper finite-window-vs-GRU current-sim high-fidelity full ideal driver and self-ID claims
- M2671 must preserve the deployable actor boundary and forbid hidden dynamics oracle labels slip tire force TTC reference trajectory path error heading error required clearance controller mode collision success progress and precomputed answers in actor input
- M2671 must not execute reset rollout replay validation training PPO source build adapter probe external simulation ranking winner selection promotion success-rate verdict or performance measurement
- M2671 must register one bounded follow-up implementation audit synthesis or stop manifest if continuing

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not fetch external source
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not execute source build
- do not execute adapter probe
- do not start a backend
- do not execute reset
- do not execute policy actions
- do not step environments
- do not execute rollout
- do not execute replay
- do not execute validation
- do not train
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not expose taxonomy labels repair target labels localization labels objective rows gate outcomes route decisions controller-family labels or paper verdict labels to actor input
- do not expose mu mass CG tire stiffness brake scale actuator time constants slip ratio slip angle tire force tire saturation friction margin AEB labels AES labels drift-required labels oracle feasibility controller mode TTC reference trajectory path error heading error required clearance path curvature collision success progress or precomputed answers to actor input
- do not rank controller families
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
- do not claim driver performance from protocol materialization

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout

## Scoreboard

- milestone: m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight
- type: infrastructure
- checkpoint: runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_protocol_materialization_result_audit
- reason: M2671 materializes Route B comparison protocol pack status_pass true with 9 controller-family rows 5 task-family rows 15 fairness-gate rows 21 claim-boundary rows and 15 gate-matrix rows includes L2 current-tiled and L3 reset/truncated controls actor 72/action 3 no hidden oracle rejects execution ranking promotion success-rate driver-performance paper FW-vs-GRU current-sim high-fidelity full ideal driver and self-ID claims routes to M2672 result audit

## Next Blocker

None recorded.
