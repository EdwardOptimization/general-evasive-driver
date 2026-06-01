# m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design Research Review

## Summary

- Generated at UTC: 20260601T192013Z
- Type: gate
- Gate tier: process
- Promotion decision: obstacle_lateral_offset_instrumentation_design_admit_implementation
- Decision reason: M2279 freezes obstacle.lateral_offset_range semantics default centerline compatibility reset-only tests materializer refresh requirements and M2280 implementation route

## Hypothesis

A backward-compatible obstacle.lateral_offset_range design can close M2277 execution blockers without changing the P0 actor contract.

## Lineage

- parent_checkpoint: not_applicable_design
- parent_dataset: docs/m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit.md, runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/summary.json, runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/unsupported_capability_rows.csv, docs/m2276-paper-route-current-sim-scenario-task-family-generation-design.md
- parent_config: experiments/manifests/m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit.json
- parent_objective: design backward-compatible emergency obstacle lateral-offset instrumentation
- derived_from: m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit
- blocked_by: M2278 accepts 38 emergency obstacle lateral-offset execution blockers
- supersedes: reset validation before lateral-offset instrumentation, silent centerline approximation of left/right obstacle rows
- invalidates: None

## Success Criteria

- docs/m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design.md exists
- field semantics and default compatibility are specified
- config builder and env reset placement effects are specified
- info/metadata/observation effects are specified
- focused implementation tests are specified
- a non-ranking implementation route is selected

## Failure Criteria

- M2279 ignores M2278 lateral-offset blockers
- M2279 changes actor input contract
- M2279 starts reset rollout measured execution training replay PPO or private holdout
- M2279 ranks profiles or selects a winner
- M2279 makes finite-window-vs-GRU paper-level or level3 self-ID claims

## Evidence Gates

- M2279 must design a backward-compatible obstacle lateral_offset_range field
- M2279 must preserve centerline default behavior and P0 actor input contract
- M2279 must define implementation tests before code changes
- M2279 must not run reset rollout measured execution training replay PPO private holdout ranking or paper/self-ID claims

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

- scenario_sampling_failure
- contract_violation
- metric_artifact

## Scoreboard

- milestone: m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design
- type: gate
- checkpoint: docs/m2279-paper-route-current-sim-obstacle-lateral-offset-instrumentation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: obstacle_lateral_offset_instrumentation_design_admit_implementation
- reason: M2279 freezes obstacle.lateral_offset_range semantics default centerline compatibility reset-only tests materializer refresh requirements and M2280 implementation route

## Next Blocker

m2280-paper-route-current-sim-obstacle-lateral-offset-instrumentation-implementation
