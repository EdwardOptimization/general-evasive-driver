# m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design Research Review

## Summary

- Generated at UTC: 20260601T195834Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_scenario_task_family_reset_repair_design_admit_combined_implementation
- Decision reason: M2286 freezes lateral sign correction sampler-aware role generation and M2287 materialization+reset-validation implementation route no reset/rollout/training claims

## Hypothesis

A combined design can repair lateral sign metadata and make R1-R5 materialization sampler-aware without changing the actor contract.

## Lineage

- parent_checkpoint: not_applicable_design
- parent_dataset: docs/m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit.md, docs/m2284-paper-route-current-sim-scenario-task-family-reset-validation-implementation.md, runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/summary.json, runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/reset_failures.csv, runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/lateral_offset_consistency_rows.csv, configs/paper_route_current_sim_scenario_task_family_v0.json
- parent_config: experiments/manifests/m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit.json
- parent_objective: design combined reset-sampling and lateral-sign repair for scenario task-family materialization
- derived_from: m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit
- blocked_by: M2285 audits M2284 reset-validation failure as R1-R5 sampling failure plus lateral sign mismatch
- supersedes: separate sign-only repair before sampler audit, direct reset rerun without materialization repair design
- invalidates: None

## Success Criteria

- docs/m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design.md exists
- lateral bucket sign correction is specified
- sampler-aware R1-R5 materialization repair is specified
- implementation tests and validation commands are specified
- a non-ranking implementation route is selected

## Failure Criteria

- M2286 ignores either reset-sampling failure or lateral sign mismatch
- M2286 changes the deployable actor contract
- M2286 starts reset rollout measured execution training replay PPO or private holdout
- M2286 ranks profiles or selects a winner
- M2286 makes finite-window-vs-GRU paper-level or level3 self-ID claims

## Evidence Gates

- M2286 must design a combined repair for reset sampling and lateral sign mismatch
- M2286 must preserve the P0 actor contract and metadata-only role labels
- M2286 must define implementation tests and validation commands before code changes
- M2286 must not run reset rollout measured execution policy actions training replay PPO private holdout ranking or paper/self-ID claims

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
- contract_violation
- metric_artifact

## Scoreboard

- milestone: m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design
- type: gate
- checkpoint: docs/m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_scenario_task_family_reset_repair_design_admit_combined_implementation
- reason: M2286 freezes lateral sign correction sampler-aware role generation and M2287 materialization+reset-validation implementation route no reset/rollout/training claims

## Next Blocker

m2287-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-implementation
