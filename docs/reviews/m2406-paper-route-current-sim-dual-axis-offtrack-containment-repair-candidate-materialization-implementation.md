# m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation Research Review

## Summary

- Generated at UTC: 20260602T130836Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: offtrack_containment_repair_candidate_materialization_pass_route_to_result_audit
- Decision reason: M2406 assigns 203/203 offtrack repair-plan rows to 4 run-dir-only overlays with guardrail metadata 8 and outside/overwrite/repair/training/ranking/guardrail 0 no verdict claims

## Hypothesis

The M2404 bounded repair-plan rows can be converted into compact run-dir-only offtrack containment repair candidate overlays with collision and R4 guardrail metadata, without active config overwrite, repair execution, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_offtrack_containment_repair_candidate_materialization
- parent_dataset: docs/m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit.md, docs/m2404-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-implementation.md, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/summary.json, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/repair_plan_rows.csv, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/offtrack_repair_plan_rows.csv, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/collision_guardrail_plan_rows.csv, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/r4_mitigation_plan_rows.csv, runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/diagnostic_monitoring_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit.json
- parent_objective: materialize compact run-dir-only offtrack containment repair candidate overlays from M2404 repair-plan rows
- derived_from: m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit, m2404-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-implementation
- blocked_by: M2397 measured outcome remains offtrack-dominated, M2405 admits exactly one bounded offtrack-containment candidate materialization route, collision and R4 guardrails must accompany any offtrack candidate
- supersedes: direct repair execution without run-dir-only candidate materialization, candidate/profile ranking from diagnostic monitoring rows, active config overwrite from repair-plan rows
- invalidates: None

## Success Criteria

- runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json exists
- candidate overlays are written only under the M2406 run directory
- candidate count is compact and non-ranking
- collision and R4 guardrail metadata are preserved
- diagnostic rows remain monitoring-only
- active_config_overwrite_count ranking_admissible_count winner_selected_count and guardrail_violation_count equal 0
- paper finite-window-vs-GRU level3 self-ID scenario-redesign training-repair and current-sim verdict claims remain false

## Failure Criteria

- M2406 reruns rollout or executes repair/training/replay/PPO
- M2406 overwrites active configs
- M2406 ranks candidates, ranks profiles, or selects a winner
- M2406 drops collision or R4 guardrail metadata
- M2406 requires actor input contract changes or hidden/oracle features
- M2406 claims scenario redesign executed, training repair success, paper result, finite-window-vs-GRU result, current-sim verdict, or level3 self-ID

## Evidence Gates

- M2406 must read only M2404 repair-plan artifacts and M2405 audit
- M2406 must materialize compact run-dir-only repair candidate overlays, not overwrite active configs
- M2406 must preserve collision and R4 guardrail metadata with each candidate
- M2406 must keep diagnostic rows non-ranking
- M2406 must not run rollout, execute repair, train, replay, run PPO, rank candidates/profiles, select a winner, or make scenario-redesign/training-repair/paper/current-sim/self-ID verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun M2397 M2399 M2401 M2404 or M2405
- do not run new rollout
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not inject hidden or oracle features
- do not tune controller profiles
- do not rank support policies or controller families
- do not rank effective candidates
- do not select a winner
- do not overwrite the active scenario config
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

- milestone: m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation
- type: infrastructure
- checkpoint: runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: offtrack_containment_repair_candidate_materialization_pass_route_to_result_audit
- reason: M2406 assigns 203/203 offtrack repair-plan rows to 4 run-dir-only overlays with guardrail metadata 8 and outside/overwrite/repair/training/ranking/guardrail 0 no verdict claims

## Next Blocker

m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit
