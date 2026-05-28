# m1352-paper-route-materialized-source-history-interpolation-preflight Research Review

## Summary

- Generated at UTC: 20260528T194605Z
- Type: gate
- Gate tier: proof
- Promotion decision: materialized_source_history_interpolation_preflight_pass_route_to_replay_result_audit
- Decision reason: M1352 selects alpha 0.005 as the only exact M267-M264 and M183-M170 passing preflight alpha; not promotion and not driver-performance evidence

## Hypothesis

A smaller interpolation of the M1346 objective direction may preserve exact source-history objective lift while avoiding M267/M264 proof washout.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
- parent_dataset: docs/m1351-paper-route-materialized-source-history-interpolation-preflight-design.md, runs/m1336_materialized_source_history_objective_corpus_export, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1351-paper-route-materialized-source-history-interpolation-preflight-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run exact plus two-surface replay preflight over M1154 to M1346 interpolation alphas
- derived_from: m1351-paper-route-materialized-source-history-interpolation-preflight-design
- blocked_by: M1351 designs the interpolation preflight but no alpha result exists
- supersedes: raw M1346 replay candidacy
- invalidates: None

## Success Criteria

- runs/m1352_materialized_source_history_interpolation_preflight/summary.json exists
- alpha_summary.csv exists and includes exact metrics plus replay outcomes
- candidate_checkpoints.csv exists
- all candidate checkpoints preserve actor input contract and allowed mutation scope
- M267/M264 replay result is recorded for every exact-admitted nonzero alpha
- M183/M170 replay result is recorded for every alpha that passes M267/M264
- no training, PPO, promotion, private holdout, threshold relaxation, full replay, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- alpha summary is missing exact or replay columns
- forbidden parameters mutate
- M267/M264 is skipped for an exact-admitted alpha
- M183/M170 is skipped for an alpha passing M267/M264
- training, PPO, private holdout, promotion, threshold relaxation, full replay, or actor-input expansion occurs

## Evidence Gates

- M1352 must not train
- M1352 must not run PPO
- M1352 must not use private holdout
- M1352 must not promote
- M1352 must preserve actor input contract
- M1352 must run exact objective metrics before replay
- M1352 must run M267/M264 before any M183/M170 replay

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not skip exact objective metrics
- do not skip M267/M264 replay for exact-admitted alphas
- do not run full public replay
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1352-paper-route-materialized-source-history-interpolation-preflight
- type: gate
- checkpoint: runs/m1352_materialized_source_history_interpolation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_interpolation_preflight_pass_route_to_replay_result_audit
- reason: M1352 selects alpha 0.005 as the only exact M267-M264 and M183-M170 passing preflight alpha; not promotion and not driver-performance evidence

## Next Blocker

m1353-paper-route-materialized-source-history-interpolation-replay-result-audit
