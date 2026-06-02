# m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel Research Review

## Summary

- Generated at UTC: 20260602T221539Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: current_sim_dual_axis_scenario_quality_discriminant_panel_pass
- Decision reason: M2452 discriminant panel pass 71 rows scenario-quality blockers 7 repair-plan candidates 19 collision guardrails 52 monitoring-only 41 guardrail violations 0 no rerun repair training ranking winner verdict claims

## Hypothesis

M2445 episode rows and M2449 target/guardrail rows can be combined into a discriminant panel that separates scenario-quality blockers from possible repair-plan candidates without rerun, repair, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_scenario_quality_discriminant_panel
- parent_dataset: docs/m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis.md, runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/episode_rows.csv, runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/target_rows.csv, runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/guardrail_rows.csv, runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/diagnostic_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis.json
- parent_objective: build an artifact-only scenario-quality discriminant panel from M2445 episodes and M2449 target/guardrail rows
- derived_from: m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis, m2450-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation-result-audit, m2449-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation
- blocked_by: M2451 closed the metric-selected validation branch and requires a new scenario-quality evidence axis, fresh measured validation is hard-offtrack dominated across a broad target surface, direct repair/training is not admitted before discriminating scenario-quality blockers from repair candidates
- supersedes: another target-table relabel in the metric-selected validation branch, direct repair/training from M2449 targets, ranking profiles, packs, families, selected checkpoints, or target rows as winners
- invalidates: None

## Success Criteria

- runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/summary.json exists
- panel rows and guardrail/decision rows are written
- profile/pack/checkpoint monitoring axes remain non-ranking
- a bounded non-ranking next route is selected or the route is stopped
- no rerun repair training ranking actual-success-improvement or verdict claim is made

## Failure Criteria

- M2452 reruns measured validation or policy action
- M2452 executes repair or training
- M2452 ranks candidate families, controller families, selected checkpoints, or target rows as winners
- M2452 selects a winner
- M2452 makes current-sim, paper, FW-vs-GRU, self-ID, scenario-redesign, or training-repair verdict claims

## Evidence Gates

- M2452 must use existing M2445 episode rows and M2449 target/guardrail rows only
- M2452 must write a new discriminant panel that separates scenario-quality blockers from possible repair-plan candidates
- M2452 must preserve profile/pack/checkpoint axes as monitoring-only and non-ranking
- M2452 must not rerun rollout, repair, train, rank, select winners, or make paper/current-sim/self-ID verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun measured policy rollout
- do not execute policy action
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not overwrite active configs
- do not change actor inputs
- do not inject hidden or oracle actor features
- do not rank candidate families
- do not rank controller families
- do not rank selected checkpoints
- do not rank target rows as winners
- do not select a winner
- do not claim actual success improvement
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel
- type: infrastructure
- checkpoint: runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/summary.json
- success_rate: 0.06685714285714285
- termination_rate: None
- clearance_margin_mean: 6.847753455149411
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_dual_axis_scenario_quality_discriminant_panel_pass
- reason: M2452 discriminant panel pass 71 rows scenario-quality blockers 7 repair-plan candidates 19 collision guardrails 52 monitoring-only 41 guardrail violations 0 no rerun repair training ranking winner verdict claims

## Next Blocker

m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel
