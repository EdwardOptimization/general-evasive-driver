# m1147-v4-public-base-row15-promoted-guarded-actor-update-probe Research Review

## Summary

- Generated at UTC: 20260527T230520Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: row15_promoted_guarded_actor_update_exact_candidate_route_to_first_replay_design
- Decision reason: M1147 finds three exact-improving contract-clean candidates; best is m1147_114602 with exact delta -0.008292 and no replay PPO or promotion

## Hypothesis

At least one low-drift actor_coupling candidate can improve or retain the exact M1144 objective while preserving anchors, allowed parameter scope, and actor-input contract.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1146-v4-public-base-row15-promoted-guarded-actor-update-design.md, runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
- parent_config: experiments/manifests/m1146-v4-public-base-row15-promoted-guarded-actor-update-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run bounded actor_coupling update probe with action and snippet anchors
- derived_from: m1146-v4-public-base-row15-promoted-guarded-actor-update-design
- blocked_by: M1146 must define guarded update contract before any actor training
- supersedes: None
- invalidates: unguarded actor update, PPO continuation from M1144 objective sanity, promotion from actor update alone

## Success Criteria

- all three candidate commands complete or failures are classified
- candidate summaries exist
- actor-input contract unchanged
- optimizer metadata confirms train_scope=actor_coupling and train_log_std=false
- changed parameters are limited to actor_mean. and response_context_fusion.0.
- at least one candidate has exact M1144 objective loss <= base exact loss
- at least one candidate has loss_mean_improvement > 0.0
- after_action_anchor_mse <= 0.0001
- after_snippet_action_anchor_mse <= 0.0001
- no PPO, replay, corpus build, objective sanity, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- all candidates fail exact objective or anchor gates
- any candidate changes forbidden parameters
- actor-input contract changes
- PPO, replay, corpus build, objective sanity, mining, promotion, or private holdout starts

## Evidence Gates

- M1147 may run only the M1146 pre-registered actor_coupling probes
- M1147 must not run PPO
- M1147 must not run replay
- M1147 must not run corpus build or objective sanity
- M1147 must not mine rows
- M1147 must not promote
- M1147 must not use private holdout
- M1147 must preserve actor inputs
- M1147 must reject any candidate changing forbidden parameters

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run replay
- do not run corpus build
- do not run objective sanity
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not chain candidates from each other
- do not weaken anchor or parameter-scope gates after seeing candidates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1147-v4-public-base-row15-promoted-guarded-actor-update-probe
- type: driver_candidate
- checkpoint: runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_guarded_actor_update_exact_candidate_route_to_first_replay_design
- reason: M1147 finds three exact-improving contract-clean candidates; best is m1147_114602 with exact delta -0.008292 and no replay PPO or promotion

## Next Blocker

m1148-v4-public-base-row15-promoted-actor-update-first-replay-design
