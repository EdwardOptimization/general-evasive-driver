# m2315-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-implementation Research Review

## Summary

- Generated at UTC: 20260601T231636Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass
- Decision reason: M2315 no-rerun diagnosis pass safe-stop metric conflict episodes 92 R0 AEB safe-stop episodes 60 residual support-blocked scenarios 18 guardrail 0 no ranking claims

## Hypothesis

No-rerun metric semantics conflict diagnosis can separate safe-stop AEB conflicts from true support-blocked scenarios.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_diagnosis
- parent_dataset: runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv, runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv, runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv, docs/m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit.md
- parent_config: experiments/manifests/m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit.json
- parent_objective: materialize no-rerun metric semantics conflict diagnosis from M2313 support-policy artifacts
- derived_from: m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit
- blocked_by: R0 AEB-feasible rows are metric_conflict 12/12, AEB support rows terminate speed_too_low with positive clearance and must be distinguished from infeasible rows
- supersedes: direct training from M2313 support labels, treating R0 metric_conflict as support_blocked, controller ranking before role-specific success semantics are audited
- invalidates: None

## Success Criteria

- src/autodrift/paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis.py exists
- tests/test_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis.py passes
- summary.json exists in the M2315 output directory
- R0 safe-stop metric conflicts are quantified
- guardrail_violation_count is 0
- a follow-up result-audit manifest is selected

## Failure Criteria

- M2315 starts new training reset rollout measured execution replay PPO or private holdout
- M2315 ranks support policies or selects a winner
- M2315 makes finite-window-vs-GRU paper-level or level3 self-ID claims
- M2315 cannot separate safe-stop metric conflicts from support-blocked rows
- M2315 cannot select a next route

## Evidence Gates

- M2315 must implement artifact-only metric semantics conflict diagnosis
- M2315 must consume M2313 episode rows and support label artifacts
- M2315 must quantify R0 safe-stop metric conflicts and role-level metric conflicts
- M2315 must not run reset rollout measured execution training replay PPO private holdout ranking or paper/self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not run replay
- do not run PPO
- do not use private holdout
- do not promote any checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m2315-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-implementation
- type: infrastructure
- checkpoint: runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass
- reason: M2315 no-rerun diagnosis pass safe-stop metric conflict episodes 92 R0 AEB safe-stop episodes 60 residual support-blocked scenarios 18 guardrail 0 no ranking claims

## Next Blocker

m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit
