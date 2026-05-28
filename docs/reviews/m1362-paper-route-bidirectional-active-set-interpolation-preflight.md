# m1362-paper-route-bidirectional-active-set-interpolation-preflight Research Review

## Summary

- Generated at UTC: 20260528T203631Z
- Type: gate
- Gate tier: proof
- Promotion decision: bidirectional_active_set_interpolation_preflight_pass_route_to_result_audit
- Decision reason: M1362 selects alpha 0.1 which passes exact M267-M264 and M183-M170 preflight with stronger exact lift than M1352 alpha 0.005

## Hypothesis

Because M1360 fails M267/M264 only by a small margin-gap regression, an interpolation alpha may preserve exact lift while satisfying M267/M264 and M183/M170 replay gates.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1360_bidirectional_active_set_probe/checkpoints/raw_bidirectional_active_set_update.pt
- parent_dataset: docs/m1361-paper-route-bidirectional-active-set-probe-result-audit.md, runs/m1360_bidirectional_active_set_probe/summary.json, runs/m1360_bidirectional_active_set_probe/replay/m267_m264/summary.json
- parent_config: experiments/manifests/m1361-paper-route-bidirectional-active-set-probe-result-audit.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: test whether a smaller alpha along the M1154 to raw M1360 direction preserves exact lift and M267/M264 plus M183/M170 replay retention
- derived_from: m1361-paper-route-bidirectional-active-set-probe-result-audit
- blocked_by: M1360 raw direction fails M267/M264 margin-gap retention by a small amount
- supersedes: direct coefficient tuning after M1360, direct gap-aware objective before amplitude preflight, direct PPO after M1360, direct promotion after M1360
- invalidates: None

## Success Criteria

- runs/m1362_bidirectional_active_set_interpolation_preflight/summary.json exists
- summary records the alpha table
- summary records exact metrics for each alpha
- summary records M267/M264 and conditional M183/M170 replay outcomes
- summary records selected alpha or no passing alpha
- no training, PPO, promotion, private holdout, threshold relaxation, full replay, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- alpha table is missing
- exact metrics are missing
- M267/M264 is skipped for exact-admitted alphas
- PPO, private holdout, promotion, threshold relaxation, full replay, training, or actor-input expansion occurs

## Evidence Gates

- M1362 must not train
- M1362 must not run PPO
- M1362 must not use private holdout
- M1362 must not promote
- M1362 must preserve actor input contract
- M1362 must evaluate exact metrics before replay for each alpha
- M1362 must run M267/M264 before M183/M170 for each admitted alpha

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not skip exact metrics
- do not skip M267/M264 before M183/M170
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1362-paper-route-bidirectional-active-set-interpolation-preflight
- type: gate
- checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_active_set_interpolation_preflight_pass_route_to_result_audit
- reason: M1362 selects alpha 0.1 which passes exact M267-M264 and M183-M170 preflight with stronger exact lift than M1352 alpha 0.005

## Next Blocker

m1363-paper-route-bidirectional-interpolation-result-audit
