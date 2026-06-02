# m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design Research Review

## Summary

- Generated at UTC: 20260602T002410Z
- Type: gate
- Gate tier: process
- Promotion decision: r4_mitigation_metric_instrumentation_design_admit_logging_field_implementation
- Decision reason: M2326 maps R4 metric gap to logging aliases and scenario CSV field export implementation no ranking claims

## Hypothesis

A bounded design can specify R4 mitigation severity instrumentation without changing actor input reward or training.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/summary.json, runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/r4_mitigation_metric_availability.csv, docs/m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit.md
- parent_config: experiments/manifests/m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit.json
- parent_objective: design R4 mitigation severity instrumentation before any role-family comparison
- derived_from: m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit
- blocked_by: R4 impact speed delta-v collision angle post-event and recoverability fields are absent, mitigation performance cannot be claimed from proxy fields, current measured execution artifacts need instrumentation before R4 comparison
- supersedes: mitigation-performance claims from proxy metrics, direct R4 controller comparison without severity fields, training from R4 residual rows
- invalidates: None

## Success Criteria

- docs/m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design.md exists
- all required R4 fields are mapped to a source or unavailable status
- the design forbids adding mitigation fields to actor input
- the design selects a bounded implementation route

## Failure Criteria

- M2326 starts new training reset rollout measured execution replay PPO or private holdout
- M2326 ranks support policies or selects a winner
- M2326 changes actor input reward or training objective
- M2326 makes finite-window-vs-GRU paper-level or level3 self-ID claims
- M2326 cannot select a next route

## Evidence Gates

- M2326 must map each required R4 mitigation field to an instrumentation source or explicit unavailable status
- M2326 must preserve the P0 human-view no-wheel no-oracle actor contract
- M2326 must not change reward or training objective
- M2326 must not run reset rollout measured execution training replay PPO private holdout ranking or paper/self-ID claims

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
- do not rank support policies or controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim residual support solved
- do not claim mitigation performance from proxy metrics alone
- do not add any mitigation field to actor input

## Failure Taxonomy

- metric_artifact
- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design
- type: gate
- checkpoint: docs/m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: r4_mitigation_metric_instrumentation_design_admit_logging_field_implementation
- reason: M2326 maps R4 metric gap to logging aliases and scenario CSV field export implementation no ranking claims

## Next Blocker

m2327-paper-route-current-sim-r4-mitigation-metric-instrumentation-implementation
