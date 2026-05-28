# m1195-paper-route-train-entrypoint-profile-mask-integration Research Review

## Summary

- Generated at UTC: 20260528T050829Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: train_entrypoint_profile_mask_integration_ready_for_stage_a_training_smoke
- Decision reason: M1195 integrates controller-profile masks into sync and parallel vector env reset/step paths plus train_ppo and evaluate_actor config discovery; focused tests show L0 vector previous-command fields are zeroed while L1 stays unchanged without training PPO replay promotion private holdout or actor-input change

## Hypothesis

Controller-profile observation masks can be applied in train/eval vector paths without changing unmasked profiles or starting training.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1194-paper-route-finite-window-gru-infrastructure-synthesis.md, src/autodrift/controller_profile_runtime.py, src/autodrift/controller_profile_runtime_smoke.py, configs/paper_route_profiles
- parent_config: experiments/manifests/m1194-paper-route-finite-window-gru-infrastructure-synthesis.json
- parent_objective: integrate controller-profile observation masks into train/eval entrypoints or vector-env construction before profile training starts
- derived_from: m1194-paper-route-finite-window-gru-infrastructure-synthesis
- blocked_by: M1194 synthesis continued the branch but kept training blocked until train/eval vector paths apply controller-profile masks
- supersedes: assuming single-env wrapper support is enough for PPO training
- invalidates: running L0 controller-profile training before vector training observations are masked

## Success Criteria

- docs/m1195-paper-route-train-entrypoint-profile-mask-integration.md exists
- focused train/eval or vector-env mask integration tests pass
- L0 vector reset and step observations zero previous-command fields 9 10 11
- unmasked profiles remain unchanged
- no hidden or oracle actor inputs are introduced
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input contract expansion occurs

## Failure Criteria

- L0 remains unmasked in train/eval vector paths
- unmasked profiles are changed
- parallel or sync behavior silently diverges without documentation
- hidden or oracle actor inputs are introduced
- controller training, candidate replay, PPO, promotion, private holdout, or actor-input expansion starts

## Evidence Gates

- M1195 may integrate controller-profile observation masks into vector env or train/eval entrypoint construction
- M1195 may add focused tests for vector reset/step masking
- M1195 must not train controller weights
- M1195 must not run PPO
- M1195 must not run candidate replay
- M1195 must not promote
- M1195 must not use private holdout
- M1195 must not add hidden or oracle actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train generated configs
- do not run PPO
- do not evaluate driver performance
- do not use private holdout
- do not change actor input semantics except applying declared deployable profile masks
- do not add hidden or oracle actor inputs
- do not claim controller performance from integration tests

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1195-paper-route-train-entrypoint-profile-mask-integration
- type: infrastructure
- checkpoint: src/autodrift/vector_env.py
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: train_entrypoint_profile_mask_integration_ready_for_stage_a_training_smoke
- reason: M1195 integrates controller-profile masks into sync and parallel vector env reset/step paths plus train_ppo and evaluate_actor config discovery; focused tests show L0 vector previous-command fields are zeroed while L1 stays unchanged without training PPO replay promotion private holdout or actor-input change

## Next Blocker

m1196-paper-route-profile-training-smoke-stage-a-run
