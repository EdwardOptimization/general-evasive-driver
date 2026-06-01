# m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization Research Review

## Summary

- Generated at UTC: 20260601T134848Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_matched_budget_medium_training_config_materialization_pass_route_to_execution
- Decision reason: M2233 medium-v1 materialization pass 15 configs 15 rows total_steps 32768 contract 0 guardrail 0 no training/ranking claims

## Hypothesis

M2232 medium-v1 design can be materialized into contract-clean configs and command artifacts without running training.

## Lineage

- parent_checkpoint: not_applicable_config_materialization
- parent_dataset: configs/paper_route_profiles/m2227_matched_budget_short_v0, docs/m2232-paper-route-current-sim-matched-budget-medium-training-design.md
- parent_config: experiments/manifests/m2232-paper-route-current-sim-matched-budget-medium-training-design.json
- parent_objective: materialize medium-v1 matched-budget profile training configs and command matrix without training
- derived_from: m2232-paper-route-current-sim-matched-budget-medium-training-design
- blocked_by: M2232 medium design must freeze profiles, seeds, budgets, readiness floors, and claim boundaries
- supersedes: manual medium-budget config edits, profile-specific medium training configs
- invalidates: None

## Success Criteria

- runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/summary.json exists
- training_matrix.csv exists
- generated configs exist for each trainable profile and seed
- all trained profiles use matched medium budgets and seeds
- total_steps is 32768 in every generated config
- contract_violation_count is 0
- training_started is false
- no reset rollout measured execution training ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- summary is missing
- training matrix is missing
- budget fields differ across profiles
- contract violations are nonzero
- new rollout or training is performed

## Evidence Gates

- M2233 must materialize exactly the M2232 five-profile three-seed medium-v1 matrix
- M2233 must set total_steps=32768 for every trainable profile/seed config
- M2233 must preserve all other matched budget fields and readiness floors
- M2233 must preserve the P0 human-view no-wheel no-oracle actor contract
- M2233 must write a training command matrix and claim boundary
- M2233 must not run reset, rollout, measured execution, policy action, training, replay, or PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit driver behavior
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- lineage_invalid
- contract_violation
- metric_artifact

## Scoreboard

- milestone: m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization
- type: infrastructure
- checkpoint: runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_matched_budget_medium_training_config_materialization_pass_route_to_execution
- reason: M2233 medium-v1 materialization pass 15 configs 15 rows total_steps 32768 contract 0 guardrail 0 no training/ranking claims

## Next Blocker

m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization
