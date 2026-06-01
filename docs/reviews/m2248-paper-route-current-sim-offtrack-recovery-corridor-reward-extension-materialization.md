# m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization Research Review

## Summary

- Generated at UTC: 20260601T155018Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_offtrack_recovery_corridor_reward_extension_materialization_pass_route_to_training_execution_design
- Decision reason: M2248 pass 15 configs budget signature 1 contract 0 track_width_widened 0 guardrail 0 no training/ranking claims

## Hypothesis

A default-preserving road-containment reward extension can materialize a matched offtrack repair config matrix without changing actor inputs or running training.

## Lineage

- parent_checkpoint: not_applicable_no_training
- parent_dataset: docs/m2247-paper-route-current-sim-task-curriculum-readiness-branch-synthesis.md, docs/m2246-paper-route-current-sim-offtrack-recovery-corridor-repair-design.md, docs/m2245-paper-route-current-sim-selected-checkpoint-outcome-localization-result-audit.md
- parent_config: runs/m2241_paper_route_current_sim_training_stability_repair_execution/configs, experiments/manifests/m2247-paper-route-current-sim-task-curriculum-readiness-branch-synthesis.json
- parent_objective: implement configurable road containment reward extension and materialize repaired matched-budget configs
- derived_from: m2247-paper-route-current-sim-task-curriculum-readiness-branch-synthesis, m2246-paper-route-current-sim-offtrack-recovery-corridor-repair-design
- blocked_by: current env has hard-coded track/heading cost and no configurable road-margin/offtrack-specific reward hook
- supersedes: track-width relaxation as primary repair, another checkpoint-selection-only repair, another blind budget escalation
- invalidates: None

## Success Criteria

- road-containment reward defaults preserve old reward behavior
- focused tests cover default compatibility and repaired config materialization
- summary artifact exists under runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization
- materialized_config_count is 15
- profile_set_matched is true
- seed_set_matched is true
- budget_signature_count is 1
- contract_violation_count is 0
- guardrail_violation_count is 0
- no reset rollout measured execution training replay PPO private holdout ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- default reward behavior changes when new fields use default values
- materialized config count is not 15
- profile set, seed set, or budget changes unexpectedly
- actor input contract changes
- track_width is widened as the primary repair
- M2248 starts training, reset, rollout, measured execution, replay, PPO, or private holdout
- M2248 ranks profiles or selects a winner

## Evidence Gates

- M2248 must preserve old reward behavior by default
- M2248 must add configurable road-containment reward fields without actor input changes
- M2248 must materialize exactly 15 repaired profile/seed configs from the M2241 config matrix
- M2248 must keep matched profile/seed/budget protocol unchanged
- M2248 must not train, run rollout, rank profiles, or select a winner

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
- do not change actor observation contract
- do not widen track_width as the primary repair
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- contract_violation
- scenario_sampling_failure
- metric_artifact
- behavior_regression

## Scoreboard

- milestone: m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization
- type: infrastructure
- checkpoint: runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_offtrack_recovery_corridor_reward_extension_materialization_pass_route_to_training_execution_design
- reason: M2248 pass 15 configs budget signature 1 contract 0 track_width_widened 0 guardrail 0 no training/ranking claims

## Next Blocker

m2248-paper-route-current-sim-offtrack-recovery-corridor-reward-extension-materialization
