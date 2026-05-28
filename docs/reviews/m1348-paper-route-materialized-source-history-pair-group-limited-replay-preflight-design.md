# m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design Research Review

## Summary

- Generated at UTC: 20260528T192553Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_source_history_limited_replay_preflight_design_admit_two_surface_preflight
- Decision reason: M1348 designs M267-M264 then M183-M170 replay preflight with direct boundary outcome replay gate

## Hypothesis

A limited public replay preflight protocol can be designed for the M1346 candidate that checks proof washout before any PPO or promotion decision.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
- parent_dataset: docs/m1347-paper-route-materialized-source-history-pair-group-update-result-audit.md, runs/m1346_materialized_source_history_pair_group_update/summary.json
- parent_config: experiments/manifests/m1347-paper-route-materialized-source-history-pair-group-update-result-audit.json
- parent_objective: design limited public replay preflight for M1346 candidate
- derived_from: m1347-paper-route-materialized-source-history-pair-group-update-result-audit
- blocked_by: M1347 admits limited replay preflight but no scoped replay protocol has been selected
- supersedes: direct PPO or promotion from M1346 objective metrics
- invalidates: None

## Success Criteria

- docs/m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design.md exists
- design specifies candidate and base checkpoints
- design specifies first preflight proof gates and stop conditions
- design specifies whether existing tooling is sufficient or adapter work is needed
- no training, PPO, promotion, private holdout, threshold relaxation, actor update, checkpoint mutation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design skips proof preflight
- design routes directly to PPO or promotion
- training, PPO, private holdout, promotion, threshold relaxation, actor update, checkpoint mutation, replay run, or actor-input expansion occurs

## Evidence Gates

- M1348 must not train
- M1348 must not run PPO
- M1348 must not use private holdout
- M1348 must not promote
- M1348 must preserve actor input contract
- M1348 must define the replay preflight tiers and stop conditions

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not skip first-row proof preflight
- do not treat objective metrics as replay proof
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design
- type: gate
- checkpoint: docs/m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_limited_replay_preflight_design_admit_two_surface_preflight
- reason: M1348 designs M267-M264 then M183-M170 replay preflight with direct boundary outcome replay gate

## Next Blocker

m1349-paper-route-materialized-source-history-pair-group-limited-replay-preflight
