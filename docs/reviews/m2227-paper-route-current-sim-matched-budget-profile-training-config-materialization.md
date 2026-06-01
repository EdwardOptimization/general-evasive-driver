# m2227-paper-route-current-sim-matched-budget-profile-training-config-materialization Research Review

## Summary

- Generated at UTC: 20260601T131442Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_matched_budget_profile_training_config_materialization_pass
- Decision reason: M2227 no-training materialization pass 15 configs 15 command rows 5 profiles 3 seeds budget matched true contract 0 guardrail 0 no reset rollout training ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

M2226 matched-budget design can be materialized into contract-clean config and command artifacts without running training.

## Lineage

- parent_checkpoint: not_applicable_config_materialization
- parent_dataset: docs/m2226-paper-route-current-sim-matched-budget-profile-training-design.md, configs/paper_route_profiles/m1190_l0_current_masked_smoke.json, configs/paper_route_profiles/m1190_l1_one_step_smoke.json, configs/paper_route_profiles/m1190_l2_window_25_smoke.json, configs/paper_route_profiles/m1190_l2_window_50_smoke.json, configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
- parent_config: experiments/manifests/m2226-paper-route-current-sim-matched-budget-profile-training-design.json
- parent_objective: materialize matched-budget profile training configs and command matrix without running training
- derived_from: m2226-paper-route-current-sim-matched-budget-profile-training-design
- blocked_by: M2226 design must freeze profile matrix, budgets, seeds, quality floors, and admission route
- supersedes: manual profile-specific training config edits, single-profile recurrent retraining configs
- invalidates: None

## Success Criteria

- runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json exists
- training_matrix.csv exists
- generated configs exist for each trainable profile and seed
- all trained profiles use matched budgets and seeds
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

- M2227 must materialize exactly the M2226 primary trainable profile matrix
- M2227 must use the same total_steps, rollout_steps, num_envs, update_epochs, minibatch_size, learning_rate, clip_coef, max_grad_norm, eval_episodes, and seed set for every trained profile
- M2227 must preserve the P0 human-view no-wheel no-oracle actor contract
- M2227 must write a training command matrix and claim boundary
- M2227 must not run reset, rollout, measured execution, policy action, training, replay, or PPO

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

- milestone: m2227-paper-route-current-sim-matched-budget-profile-training-config-materialization
- type: infrastructure
- checkpoint: runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_matched_budget_profile_training_config_materialization_pass
- reason: M2227 no-training materialization pass 15 configs 15 command rows 5 profiles 3 seeds budget matched true contract 0 guardrail 0 no reset rollout training ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2227-paper-route-current-sim-matched-budget-profile-training-config-materialization
