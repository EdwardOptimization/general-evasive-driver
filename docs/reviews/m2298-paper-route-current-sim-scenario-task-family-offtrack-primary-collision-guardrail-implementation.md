# m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation Research Review

## Summary

- Generated at UTC: 20260601T211443Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass
- Decision reason: M2298 materializes offtrack targets 20 collision guardrails 11 profile target/guardrail 0 repair_gate_spec true no rerun/ranking claims

## Hypothesis

M2297 rules can materialize non-profile offtrack target slices and collision guardrail slices suitable for a later guarded repair design.

## Lineage

- parent_checkpoint: not_applicable_artifact_materialization
- parent_dataset: docs/m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design.md, runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/all_slices.csv, runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv, runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/route_recommendation.csv
- parent_config: experiments/manifests/m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design.json
- parent_objective: materialize offtrack target slices and collision guardrail slices from M2295 diagnosis
- derived_from: m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design
- blocked_by: M2297 selects target/guardrail materialization before any repair or training
- supersedes: direct broad PPO/reward repair before target materialization, profile-axis target selection
- invalidates: None

## Success Criteria

- runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json exists
- offtrack_target_slice_count is at least 8
- collision_guardrail_slice_count is at least 3
- profile_target_slice_count equals 0
- profile_guardrail_slice_count equals 0
- repair_gate_spec.json exists
- no reset rollout training ranking paper-level finite-window-vs-GRU or self-ID claim is made

## Failure Criteria

- M2298 runs reset or rollout
- M2298 trains or changes scenario/profile configs
- M2298 admits profile_name/profile_seed target or guardrail slices
- M2298 cannot write repair_gate_spec.json
- M2298 ranks profiles or selects a winner
- M2298 makes paper-level finite-window-vs-GRU or level3 self-ID claims

## Evidence Gates

- M2298 must consume M2295 slice artifacts only
- M2298 must not run reset, rollout, policy action, training, replay, or PPO
- M2298 must exclude profile_name and profile_seed axes from target and guardrail materialization
- M2298 must write offtrack target slices, collision guardrail slices, and repair_gate_spec.json
- M2298 must not rank profiles or claim paper/self-ID evidence

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
- metric_artifact
- objective_overfit

## Scoreboard

- milestone: m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation
- type: infrastructure
- checkpoint: runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json
- success_rate: 0.06388888888888888
- termination_rate: None
- clearance_margin_mean: 6.802372067958403
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass
- reason: M2298 materializes offtrack targets 20 collision guardrails 11 profile target/guardrail 0 repair_gate_spec true no rerun/ranking claims

## Next Blocker

m2299-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-result-audit
