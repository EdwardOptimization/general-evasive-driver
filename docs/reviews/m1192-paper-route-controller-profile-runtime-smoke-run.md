# m1192-paper-route-controller-profile-runtime-smoke-run Research Review

## Summary

- Generated at UTC: 20260528T044546Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controller_profile_runtime_smoke_pass_route_to_training_smoke_design
- Decision reason: M1192 instantiates all eight generated L0/L1/L2/L3 configs with runtime masks and ActorCritic models; L0 raw previous-command sum 1.45 becomes 0.0 under wrapper and unmasked profiles remain unchanged without training PPO replay promotion private holdout or actor-input change

## Hypothesis

Generated L0/L1/L2/L3 configs can instantiate with runtime mask handling and no hidden/oracle actor inputs before training starts.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1191-paper-route-observation-mask-runtime-wrapper-implementation.md, src/autodrift/controller_profile_runtime.py, configs/paper_route_profiles
- parent_config: experiments/manifests/m1191-paper-route-observation-mask-runtime-wrapper-implementation.json
- parent_objective: instantiate generated controller-profile configs with runtime observation masking and no training
- derived_from: m1191-paper-route-observation-mask-runtime-wrapper-implementation
- blocked_by: profile configs and runtime masks exist but have not been smoke-instantiated together across all profiles
- supersedes: assuming generated configs are runnable because unit tests pass
- invalidates: starting profile training before all generated configs instantiate cleanly with runtime mask handling

## Success Criteria

- docs/m1192-paper-route-controller-profile-runtime-smoke-run.md exists
- runs/m1192_controller_profile_runtime_smoke/summary.json exists
- all eight generated configs instantiate
- L0 reset and step observations are masked
- unmasked profiles are unchanged
- summary reports training_started false and ppo_used false
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input contract change occurs

## Failure Criteria

- any generated config cannot instantiate
- L0 runtime mask is not observed
- unmasked profiles are changed
- smoke starts training or PPO
- hidden or oracle actor inputs are introduced

## Evidence Gates

- M1192 may implement a no-training runtime smoke runner if needed
- M1192 may instantiate envs, wrappers, and ActorCritic models for generated profile configs
- M1192 must not train controller weights
- M1192 must not run PPO
- M1192 must not run candidate replay
- M1192 must not promote
- M1192 must not use private holdout
- M1192 must not add hidden or oracle actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train generated configs
- do not run PPO
- do not evaluate driver performance
- do not use private holdout
- do not change actor inputs
- do not add hidden or oracle actor inputs
- do not claim controller performance from smoke instantiation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1192-paper-route-controller-profile-runtime-smoke-run
- type: infrastructure
- checkpoint: runs/m1192_controller_profile_runtime_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controller_profile_runtime_smoke_pass_route_to_training_smoke_design
- reason: M1192 instantiates all eight generated L0/L1/L2/L3 configs with runtime masks and ActorCritic models; L0 raw previous-command sum 1.45 becomes 0.0 under wrapper and unmasked profiles remain unchanged without training PPO replay promotion private holdout or actor-input change

## Next Blocker

m1193-paper-route-controller-profile-training-smoke-design
