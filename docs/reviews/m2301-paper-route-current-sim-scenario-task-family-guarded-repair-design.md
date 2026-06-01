# m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design Research Review

## Summary

- Generated at UTC: 20260601T212930Z
- Type: gate
- Gate tier: process
- Promotion decision: guarded_repair_design_admit_config_materialization
- Decision reason: M2301 admits 15-config shared guarded repair materialization using M2298 target/guardrail gates no reset/training/ranking claims

## Hypothesis

A guarded repair design can convert M2298 offtrack targets and collision guardrails into a bounded non-ranking repair route without changing actor inputs or scenario specs.

## Lineage

- parent_checkpoint: not_applicable_design_gate
- parent_dataset: docs/m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.md, runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json, runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/offtrack_target_slices.csv, runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/collision_guardrail_slices.csv, runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json
- parent_config: experiments/manifests/m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.json
- parent_objective: design guarded repair route using M2298 offtrack targets and collision guardrails
- derived_from: m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis
- blocked_by: M2300 synthesis continues to guarded repair design and requires new measurable evidence quickly
- supersedes: direct broad reward repair before synthesis, profile-specific repair target selection
- invalidates: None

## Success Criteria

- docs/m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design.md exists
- M2301 freezes offtrack target improvement gates from M2298
- M2301 freezes collision guardrail non-regression gates from M2298
- M2301 names allowed repair knobs and blocked shortcuts
- M2301 pre-registers one non-ranking follow-up implementation route

## Failure Criteria

- M2301 runs reset or rollout
- M2301 trains or runs PPO
- M2301 changes actor inputs or scenario specs
- M2301 uses profile_name/profile_seed as repair targets
- M2301 ranks profiles or selects a winner
- M2301 makes paper-level finite-window-vs-GRU or level3 self-ID claims
- M2301 cannot select a next route

## Evidence Gates

- M2301 must not run reset or rollout
- M2301 must not train or run PPO
- M2301 must preserve P0 actor input contract
- M2301 must use M2298 offtrack targets as repair objectives
- M2301 must use M2298 collision guardrails as non-regression constraints
- M2301 must freeze a non-ranking implementation route for the next milestone
- M2301 must not rank profiles, select a winner, or claim paper/self-ID evidence

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
- do not use profile_name or profile_seed as repair targets
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

- milestone: m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design
- type: gate
- checkpoint: docs/m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design.md
- success_rate: 0.06388888888888888
- termination_rate: None
- clearance_margin_mean: 6.802372067958403
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_repair_design_admit_config_materialization
- reason: M2301 admits 15-config shared guarded repair materialization using M2298 target/guardrail gates no reset/training/ranking claims

## Next Blocker

m2302-paper-route-current-sim-scenario-task-family-guarded-repair-config-materialization
