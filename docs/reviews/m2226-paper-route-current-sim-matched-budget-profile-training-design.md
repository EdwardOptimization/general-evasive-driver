# m2226-paper-route-current-sim-matched-budget-profile-training-design Research Review

## Summary

- Generated at UTC: 20260601T130300Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_matched_budget_profile_training_design_admit_config_materialization
- Decision reason: M2226 freezes matched-budget primary profile training design L0 L1 L2_25 L2_50 L3_online 3 seeds 8192 steps quality floors and post-training gates no training/ranking claims

## Hypothesis

A matched-budget training design can remove the weak-smoke checkpoint blocker without overclaiming finite-window or GRU evidence.

## Lineage

- parent_checkpoint: not_applicable_training_design
- parent_dataset: docs/m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit.md, runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit/summary.json, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit.json
- parent_objective: freeze matched-budget L0/L1/L2/L3 training design before any new training or comparison
- derived_from: m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit
- blocked_by: M2224 confirms L3 smoke checkpoint is weak and matched-budget training is needed
- supersedes: single-profile L3 retraining without matched-budget controller matrix, direct measured rerun from weak smoke checkpoints
- invalidates: None

## Success Criteria

- docs/m2226-paper-route-current-sim-matched-budget-profile-training-design.md exists
- design defines profile matrix, budgets, seeds, quality floors, checkpoint materialization, readiness, reset/runtime smoke, and post-training route
- design preserves actor input contract
- no reset rollout measured execution training ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design document is missing
- design trains only L3 without matched profile budgets
- design allows hidden/oracle inputs
- design allows ranking before admission gates
- new rollout or training is performed

## Evidence Gates

- M2226 must define a matched-budget L0/L1/L2/L3 training matrix
- M2226 must preserve the P0 human-view no-wheel no-oracle actor contract
- M2226 must specify seed policy, training budget, quality floors, checkpoint materialization, readiness, and reset/runtime smoke admission gates
- M2226 must explicitly block profile-specific tuning, ranking, paper claims, finite-window-vs-GRU verdicts, and self-ID claims
- M2226 must not run reset, rollout, measured execution, policy action, training, replay, or PPO

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

- seed_fragility
- training_instability
- metric_artifact

## Scoreboard

- milestone: m2226-paper-route-current-sim-matched-budget-profile-training-design
- type: gate
- checkpoint: docs/m2226-paper-route-current-sim-matched-budget-profile-training-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_matched_budget_profile_training_design_admit_config_materialization
- reason: M2226 freezes matched-budget primary profile training design L0 L1 L2_25 L2_50 L3_online 3 seeds 8192 steps quality floors and post-training gates no training/ranking claims

## Next Blocker

m2226-paper-route-current-sim-matched-budget-profile-training-design
