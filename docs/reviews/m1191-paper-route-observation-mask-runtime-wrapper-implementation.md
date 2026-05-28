# m1191-paper-route-observation-mask-runtime-wrapper-implementation Research Review

## Summary

- Generated at UTC: 20260528T043744Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: runtime_observation_mask_ready_route_to_profile_runtime_smoke
- Decision reason: M1191 implements runtime observation-mask support so L0 zeros previous-command fields 9/10/11 at reset and step while L1/L2 unmasked profiles remain unchanged; focused runtime/config/profile tests pass without training PPO replay promotion private holdout or actor-input change

## Hypothesis

Runtime observation masking can make L0_current_masked executable without changing unmasked profiles or introducing oracle inputs.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1190-paper-route-controller-profile-config-generation-implementation.md, src/autodrift/controller_profiles.py, src/autodrift/controller_profile_configs.py, configs/paper_route_profiles/m1190_l0_current_masked_smoke.json
- parent_config: experiments/manifests/m1190-paper-route-controller-profile-config-generation-implementation.json
- parent_objective: implement runtime observation mask support so L0_current_masked actually zeros previous command fields before training or evaluation
- derived_from: m1190-paper-route-controller-profile-config-generation-implementation
- blocked_by: M1190 config metadata records L0 mask but current runtime entrypoints do not apply it
- supersedes: treating L0 metadata as if the mask is applied at runtime
- invalidates: running L0 training or evaluation before runtime mask support exists

## Success Criteria

- runtime mask adapter exists
- focused runtime mask tests pass
- L0 zeros previous-command fields 9 10 11 at runtime
- unmasked profiles remain unchanged
- no hidden or oracle actor inputs are introduced
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input contract change occurs

## Failure Criteria

- L0 mask is metadata-only after M1191
- mask zeros wrong fields
- unmasked profiles are changed
- hidden or oracle actor inputs are introduced
- controller training, candidate replay, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1191 may implement runtime observation masking and focused tests only
- M1191 must not train controller weights
- M1191 must not run PPO
- M1191 must not run candidate replay
- M1191 must not promote
- M1191 must not use private holdout
- M1191 must not add hidden or oracle actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train generated configs
- do not run PPO
- do not use private holdout
- do not change actor input semantics beyond applying declared deployable masks
- do not add hidden or oracle actor inputs
- do not claim controller performance from wrapper tests

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1191-paper-route-observation-mask-runtime-wrapper-implementation
- type: infrastructure
- checkpoint: src/autodrift/controller_profile_runtime.py
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: runtime_observation_mask_ready_route_to_profile_runtime_smoke
- reason: M1191 implements runtime observation-mask support so L0 zeros previous-command fields 9/10/11 at reset and step while L1/L2 unmasked profiles remain unchanged; focused runtime/config/profile tests pass without training PPO replay promotion private holdout or actor-input change

## Next Blocker

m1192-paper-route-controller-profile-runtime-smoke-run
