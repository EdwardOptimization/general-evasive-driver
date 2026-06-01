# m2313-paper-route-current-sim-scenario-task-family-feasibility-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260601T230441Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: current_sim_scenario_task_family_feasibility_calibration_pass
- Decision reason: M2313 support-policy calibration pass 1080 episodes failure 0 support labels clear/mixed/blocked/metric 12/26/21/13 R0 metric_conflict 12/12 no ranking claims

## Hypothesis

A support-policy diagnostic panel can separate scenario feasibility/support from actor weakness without ranking controllers.

## Lineage

- parent_checkpoint: not_applicable_support_policy_diagnostic_panel
- parent_dataset: configs/paper_route_current_sim_scenario_task_family_v0.json, docs/m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design.md, docs/m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.md, runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json, runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json, runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/summary.json
- parent_config: experiments/manifests/m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design.json
- parent_objective: implement and run no-ranking support-policy feasibility calibration panel
- derived_from: m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design
- blocked_by: current scenario task family has not separated feasibility from actor weakness, controller-family ranking remains blocked until support calibration is audited
- supersedes: another guarded-v2 scalar reward tweak, direct controller-family comparison before support calibration
- invalidates: None

## Success Criteria

- src/autodrift/paper_route_current_sim_scenario_task_family_feasibility_calibration.py exists
- tests/test_paper_route_current_sim_scenario_task_family_feasibility_calibration.py passes
- summary.json exists in the M2313 output directory
- episode_count is 1080
- scenario_spec_count is 72
- support_policy_count is 3
- seed_repeat_count is 5
- ranking_admissible_count is 0
- guardrail_violation_count is 0
- a follow-up result-audit manifest is selected

## Failure Criteria

- M2313 starts training replay PPO private holdout or promotion
- M2313 ranks support policies or selects a winner
- M2313 makes finite-window-vs-GRU paper-level or level3 self-ID claims
- M2313 omits support labels or role support aggregates
- M2313 cannot preserve the 1080-episode denominator without fail-closed artifacts

## Evidence Gates

- M2313 must implement a support-policy diagnostic runner
- M2313 must run 72 scenario specs x 3 support policies x 5 seed repeats = 1080 episodes
- M2313 must write support labels and role support aggregates
- M2313 must keep ranking_admissible false and winner_selected false
- M2313 must not train replay PPO promote private holdout rank controllers or make paper/self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run replay
- do not run PPO
- do not use private holdout
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not treat support policies as deployable candidates
- do not compare support policies as winners

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- behavior_regression

## Scoreboard

- milestone: m2313-paper-route-current-sim-scenario-task-family-feasibility-calibration-implementation
- type: infrastructure
- checkpoint: runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/summary.json
- success_rate: 0.09907407407407408
- termination_rate: None
- clearance_margin_mean: 5.430327544891803
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_feasibility_calibration_pass
- reason: M2313 support-policy calibration pass 1080 episodes failure 0 support labels clear/mixed/blocked/metric 12/26/21/13 R0 metric_conflict 12/12 no ranking claims

## Next Blocker

m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit
