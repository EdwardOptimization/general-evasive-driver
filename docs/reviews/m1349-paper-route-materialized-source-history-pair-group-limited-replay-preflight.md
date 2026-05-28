# m1349-paper-route-materialized-source-history-pair-group-limited-replay-preflight Research Review

## Summary

- Generated at UTC: 20260528T192956Z
- Type: gate
- Gate tier: proof
- Promotion decision: materialized_source_history_limited_replay_preflight_m267_m264_proof_washout_route_to_failure_audit
- Decision reason: M1349 rejects M1346 replay candidacy because M267-M264 normal success collapses from 1.0 to 0.0

## Hypothesis

The M1346 objective-positive candidate may retain the two most relevant public proof replay surfaces, M267/M264 and M183/M170, relative to M1154.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
- parent_dataset: docs/m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design.md, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run two-surface public replay preflight for M1346 candidate
- derived_from: m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight-design
- blocked_by: M1348 designs a two-surface replay preflight but no replay result exists
- supersedes: promotion or PPO from fixed source-history objective metrics
- invalidates: None

## Success Criteria

- runs/m1349_materialized_source_history_limited_replay_preflight/summary.json exists
- M267/M264 replay result is recorded
- M183/M170 replay result is recorded if M267/M264 passes
- actor input contract is unchanged
- no PPO, promotion, private holdout, threshold relaxation, training, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- M267/M264 result is missing
- M183/M170 is skipped after M267/M264 passes
- M1349 runs full replay after first-surface failure
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1349 must not train
- M1349 must not run PPO
- M1349 must not use private holdout
- M1349 must not promote
- M1349 must preserve actor input contract
- M1349 must run M267/M264 before M183/M170
- M1349 must stop after the first failed proof surface

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not skip M267/M264 preflight
- do not run full public replay after first-surface failure
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1349-paper-route-materialized-source-history-pair-group-limited-replay-preflight
- type: gate
- checkpoint: runs/m1349_materialized_source_history_limited_replay_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_limited_replay_preflight_m267_m264_proof_washout_route_to_failure_audit
- reason: M1349 rejects M1346 replay candidacy because M267-M264 normal success collapses from 1.0 to 0.0

## Next Blocker

m1350-paper-route-materialized-source-history-pair-group-replay-failure-audit
