# m1351-paper-route-materialized-source-history-interpolation-preflight-design Research Review

## Summary

- Generated at UTC: 20260528T193658Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_source_history_interpolation_preflight_design_admit_implementation
- Decision reason: M1351 designs small-alpha exact-plus-replay interpolation preflight for M1154 to M1346 direction

## Hypothesis

A trust-region interpolation protocol can determine whether the M1346 objective direction has a usable small-alpha region before replay-aware repair.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
- parent_dataset: docs/m1350-paper-route-materialized-source-history-pair-group-replay-failure-audit.md, runs/m1346_materialized_source_history_pair_group_update/summary.json, runs/m1349_materialized_source_history_limited_replay_preflight/summary.json
- parent_config: experiments/manifests/m1350-paper-route-materialized-source-history-pair-group-replay-failure-audit.json
- parent_objective: design interpolation trust-region replay preflight for M1346 update direction
- derived_from: m1350-paper-route-materialized-source-history-pair-group-replay-failure-audit
- blocked_by: M1350 rejects raw M1346 but leaves open whether a smaller interpolation preserves replay while improving exact objective metrics
- supersedes: direct replay-aware repair before checking alpha trust region
- invalidates: None

## Success Criteria

- docs/m1351-paper-route-materialized-source-history-interpolation-preflight-design.md exists
- design specifies interpolation alphas
- design specifies exact source-history metric gates before replay
- design specifies M267/M264 and conditional M183/M170 replay gates
- no training, PPO, promotion, private holdout, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits M267/M264
- design routes directly to PPO or promotion
- training, PPO, private holdout, promotion, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Evidence Gates

- M1351 must not train
- M1351 must not run PPO
- M1351 must not use private holdout
- M1351 must not promote
- M1351 must preserve actor input contract
- M1351 must design exact objective and replay gates for interpolated candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not skip exact objective checks
- do not skip M267/M264 replay
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1351-paper-route-materialized-source-history-interpolation-preflight-design
- type: gate
- checkpoint: docs/m1351-paper-route-materialized-source-history-interpolation-preflight-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_interpolation_preflight_design_admit_implementation
- reason: M1351 designs small-alpha exact-plus-replay interpolation preflight for M1154 to M1346 direction

## Next Blocker

m1352-paper-route-materialized-source-history-interpolation-preflight
