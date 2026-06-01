# m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design Research Review

## Summary

- Generated at UTC: 20260601T210715Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_offtrack_target_collision_guardrail_materialization
- Decision reason: M2297 designs non-profile offtrack target and collision guardrail materialization route no rerun/training/ranking claims

## Hypothesis

A design-only route can convert M2295/M2296 offtrack-primary collision-guardrail evidence into a concrete non-ranking implementation plan.

## Lineage

- parent_checkpoint: not_applicable_design
- parent_dataset: docs/m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit.md, runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/summary.json, runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv, runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv
- parent_config: experiments/manifests/m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit.json
- parent_objective: design offtrack-primary collision-guardrail next route after M2295/M2296
- derived_from: m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit
- blocked_by: M2296 accepts M2295 offtrack-primary collision-guardrail diagnosis and blocks direct repair/ranking
- supersedes: direct broad reward repair from global offtrack rate, direct profile ranking from diagnostic aggregates
- invalidates: None

## Success Criteria

- docs/m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design.md exists
- target offtrack slices are listed
- collision guardrail slices are listed
- next implementation route is selected
- pass/fail gates are defined for the next route
- no reset rollout training ranking paper-level finite-window-vs-GRU or self-ID claim is made

## Failure Criteria

- M2297 reruns reset or rollout
- M2297 trains or changes scenario/profile configs
- M2297 ranks profiles or selects a winner
- M2297 makes paper-level finite-window-vs-GRU or level3 self-ID claims
- M2297 cannot select a next route

## Evidence Gates

- M2297 must be design-only
- M2297 must define target offtrack slices and collision guardrail slices from M2295
- M2297 must choose a non-ranking implementation route
- M2297 must not run reset, rollout, training, replay, PPO, or private holdout
- M2297 must not rank profiles or claim paper/self-ID evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change scenario specs
- do not change profile configs
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- behavior_regression
- objective_overfit
- metric_artifact

## Scoreboard

- milestone: m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design
- type: gate
- checkpoint: docs/m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design.md
- success_rate: 0.06388888888888888
- termination_rate: None
- clearance_margin_mean: 6.802372067958403
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_offtrack_target_collision_guardrail_materialization
- reason: M2297 designs non-profile offtrack target and collision guardrail materialization route no rerun/training/ranking claims

## Next Blocker

m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation
