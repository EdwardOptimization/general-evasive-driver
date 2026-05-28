# m1190-paper-route-controller-profile-config-generation-implementation Research Review

## Summary

- Generated at UTC: 20260528T043001Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controller_profile_configs_generated_route_to_runtime_mask_wrapper
- Decision reason: M1190 generates eight profile smoke configs and focused contract tests with L0 mask metadata while blocking actual training replay PPO promotion private holdout or actor-input change

## Hypothesis

Generated smoke configs can preserve L0/L1/L2/L3 profile metadata and the no-oracle actor contract without starting training.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1189-paper-route-controller-profile-config-generation-design.md, src/autodrift/controller_profiles.py, configs/m121_human_view_zero_obstacle_relvel.json
- parent_config: experiments/manifests/m1189-paper-route-controller-profile-config-generation-design.json
- parent_objective: implement generated smoke configs and contract checks for L0 L1 L2 L3 profiles without running training
- derived_from: m1189-paper-route-controller-profile-config-generation-design
- blocked_by: profile metadata exists but generated contract-clean smoke configs do not
- supersedes: manual profile config editing
- invalidates: starting training from hand-written profile configs before generation tests exist

## Success Criteria

- config generation module exists
- focused config generation tests pass
- eight profile smoke configs are generated
- L0 config includes previous-command mask metadata
- L2 configs cover 13 25 50 and 100 step windows
- summary artifact reports training_started false and ppo_used false
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- generated configs include hidden or oracle actor inputs
- L0 mask metadata is missing
- finite-window profiles are omitted
- generated configs are executed for training
- actor-input contract changes

## Evidence Gates

- M1190 may generate config files and contract tests only
- M1190 must not run generated train configs
- M1190 must not train controller weights
- M1190 must not run PPO
- M1190 must not run candidate replay
- M1190 must not promote
- M1190 must not use private holdout
- M1190 must not add hidden or oracle actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train generated configs
- do not run PPO
- do not use private holdout
- do not change actor inputs
- do not generate hidden or oracle actor inputs
- do not claim controller performance from config generation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1190-paper-route-controller-profile-config-generation-implementation
- type: infrastructure
- checkpoint: runs/m1190_controller_profile_config_generation/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controller_profile_configs_generated_route_to_runtime_mask_wrapper
- reason: M1190 generates eight profile smoke configs and focused contract tests with L0 mask metadata while blocking actual training replay PPO promotion private holdout or actor-input change

## Next Blocker

m1191-paper-route-observation-mask-runtime-wrapper-implementation
