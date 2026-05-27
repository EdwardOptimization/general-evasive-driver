# m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe Research Review

## Summary

- Generated at UTC: 20260527T211059Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: failed_wrong_history_retention_actor_update_exact_candidate_route_to_first_replay_design
- Decision reason: M1118 runs three retention-aware actor_coupling seeds and all pass pre-replay exact anchor and parameter gates with best seed111800 loss improvement 0.003012 and target-base trajectory MSE 0.000001498

## Hypothesis

A lower-lr actor-coupling update with M1115 trajectory retention can improve or retain exact M1107 objective while keeping target-base wrong-history trajectory actions close to the current public base.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz, runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz, runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.npz, docs/m1116-v4-public-base-failed-wrong-history-retention-actor-update-design.md, docs/m1117-v4-public-base-materialized-objective-branch-synthesis.md
- parent_config: experiments/manifests/m1117-v4-public-base-materialized-objective-branch-synthesis.json
- parent_objective: run bounded actor-coupling update with M1107 exact objective and M1115 trajectory retention
- derived_from: m1116-v4-public-base-failed-wrong-history-retention-actor-update-design, m1117-v4-public-base-materialized-objective-branch-synthesis
- blocked_by: M1112 proof washout requires rejected-history trajectory retention before replay, M1117 opens failed_wrong_history_retention_repair branch
- supersedes: None
- invalidates: exact-objective-only actor update, PPO before retention-aware actor-update probe, replay before exact and anchor pre-gates

## Success Criteria

- exactly three seeds 111800 111801 111802 are run
- train_scope is actor_coupling and log_std is frozen
- only actor_mean. and response_context_fusion.0. parameters change
- M1107 exact objective no-regression is measured
- combined trajectory-action-anchor MSE is measured
- target-base-only trajectory-action-anchor MSE is measured
- at least one candidate passes exact and anchor pre-replay gates or the failure is classified
- no PPO, replay, promotion, private holdout, actor-input change, or short-family hidden-state training anchor is used

## Failure Criteria

- optimizer command fails for all seeds
- any candidate changes forbidden parameter groups
- all candidates regress exact M1107 objective
- all candidates regress trajectory-anchor retention beyond threshold
- PPO, replay, promotion, private holdout, actor-input change, or short-family hidden-state training anchor is used

## Evidence Gates

- M1118 may run exactly three actor-coupling optimizer candidates from the current public-gate base
- M1118 must use M1107 exact objective and M1115 combined trajectory retention
- M1118 must keep log_std frozen
- M1118 must not run PPO
- M1118 must not run replay
- M1118 must not promote
- M1118 must not use private holdout
- M1118 must preserve actor inputs
- M1118 must not use short-family hidden states as training anchors

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run replay
- do not promote
- do not use private holdout
- do not change actor inputs
- do not train log_std
- do not change parameters outside actor_mean. and response_context_fusion.0.
- do not use short-family hidden states as training anchors
- do not add extra seeds or coefficient search after seeing failures

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe
- type: driver_candidate
- checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: failed_wrong_history_retention_actor_update_exact_candidate_route_to_first_replay_design
- reason: M1118 runs three retention-aware actor_coupling seeds and all pass pre-replay exact anchor and parameter gates with best seed111800 loss improvement 0.003012 and target-base trajectory MSE 0.000001498

## Next Blocker

m1119-v4-public-base-failed-wrong-history-retention-first-replay-design
