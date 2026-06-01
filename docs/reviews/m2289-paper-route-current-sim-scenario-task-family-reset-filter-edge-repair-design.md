# m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design Research Review

## Summary

- Generated at UTC: 20260601T201930Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_scenario_task_family_filter_edge_repair_design_admit_implementation
- Decision reason: M2289 freezes v0 reset-valid pack with friction_step disabled for all specs plus reset-filter precheck helper route to M2290 no reset/ranking claims

## Hypothesis

A focused design can make materializer precheck match reset sampler friction-step filters without changing actor inputs or role semantics.

## Lineage

- parent_checkpoint: not_applicable_design
- parent_dataset: docs/m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit.md, docs/m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation.md, runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation/summary.json, runs/m2287_paper_route_current_sim_reset_sampling_lateral_sign_repair/reset_validation/reset_failures.csv, configs/paper_route_current_sim_scenario_task_family_v0.json
- parent_config: experiments/manifests/m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit.json
- parent_objective: design focused materializer repair for friction-step timing filter edge
- derived_from: m2288-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-result-audit
- blocked_by: M2288 localizes M2287's remaining reset failure to a friction-step timing filter omitted from materializer precheck
- supersedes: direct repair/rerun before filter-edge design, measured execution after 71/72 reset validation
- invalidates: None

## Success Criteria

- docs/m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design.md exists
- friction-step timing filter compatibility repair is specified
- implementation tests and validation commands are specified
- a non-ranking implementation route is selected

## Failure Criteria

- M2289 ignores the M2288 friction-step timing filter finding
- M2289 changes the deployable actor contract
- M2289 starts reset rollout measured execution training replay PPO or private holdout
- M2289 ranks profiles or selects a winner
- M2289 makes finite-window-vs-GRU paper-level or level3 self-ID claims

## Evidence Gates

- M2289 must design a focused repair for friction-step timing filter compatibility
- M2289 must preserve role labels, P0 actor contract, and metadata-only feasibility labels
- M2289 must freeze implementation tests and materialization/reset-validation commands before code changes
- M2289 must not run reset rollout measured execution policy actions training replay PPO private holdout ranking or paper/self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design
- type: gate
- checkpoint: docs/m2289-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 0.9861111111111112
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_filter_edge_repair_design_admit_implementation
- reason: M2289 freezes v0 reset-valid pack with friction_step disabled for all specs plus reset-filter precheck helper route to M2290 no reset/ranking claims

## Next Blocker

m2290-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-implementation
