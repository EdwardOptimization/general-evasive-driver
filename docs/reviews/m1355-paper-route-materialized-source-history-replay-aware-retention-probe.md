# m1355-paper-route-materialized-source-history-replay-aware-retention-probe Research Review

## Summary

- Generated at UTC: 20260528T200250Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: materialized_source_history_replay_aware_retention_m267_proof_washout_route_to_branch_synthesis
- Decision reason: M1355 strongly improves exact metrics but fails M267-M264 because five wrong-history rows become successful; normal retention alone is insufficient

## Hypothesis

Replay-aware retention can preserve M267/M264 and M183/M170 while producing more exact source-history progress than the diagnostic alpha 0.005 interpolation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt, runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt
- parent_dataset: docs/m1354-paper-route-materialized-source-history-replay-aware-retention-design.md, runs/m1336_materialized_source_history_objective_corpus_export, runs/m1352_materialized_source_history_interpolation_preflight/replay/m1352_alpha_0_005/m267_m264/boundary_replay_rows.csv, runs/m1352_materialized_source_history_interpolation_preflight/replay/m1352_alpha_0_005/m183_m170/boundary_replay_rows.csv, runs/m1352_materialized_source_history_interpolation_preflight/alpha_summary.csv
- parent_config: experiments/manifests/m1354-paper-route-materialized-source-history-replay-aware-retention-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run one bounded no-PPO source-history update with replay-aware retention active set
- derived_from: m1354-paper-route-materialized-source-history-replay-aware-retention-design
- blocked_by: M1354 designs the retention objective but no retained update has been run
- supersedes: pure interpolation-only continuation, direct PPO continuation, direct full replay of alpha 0.005
- invalidates: None

## Success Criteria

- runs/m1355_materialized_source_history_replay_aware_retention_probe/summary.json exists
- summary records retention active-set rows and weights
- summary records mutation scope and actor input contract checks
- summary records exact source-history metrics versus M1154 and alpha 0.005
- summary records M267/M264 and conditional M183/M170 replay outcomes
- no PPO, promotion, private holdout, threshold relaxation, full replay, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- retention active-set rows are not recorded
- mutation or actor contract checks are missing
- exact metrics are missing
- M267/M264 is skipped before M183/M170
- PPO, private holdout, promotion, threshold relaxation, full replay, or actor-input expansion occurs

## Evidence Gates

- M1355 must not run PPO
- M1355 must not use private holdout
- M1355 must not promote
- M1355 must preserve actor input contract
- M1355 must verify allowed mutation scope
- M1355 must evaluate exact source-history metrics before replay
- M1355 must run M267/M264 before M183/M170
- M1355 must route to synthesis after result

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not skip mutation checks
- do not skip exact metrics
- do not skip M267/M264 before M183/M170
- do not run full public replay
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1355-paper-route-materialized-source-history-replay-aware-retention-probe
- type: infrastructure
- checkpoint: runs/m1355_materialized_source_history_replay_aware_retention_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_replay_aware_retention_m267_proof_washout_route_to_branch_synthesis
- reason: M1355 strongly improves exact metrics but fails M267-M264 because five wrong-history rows become successful; normal retention alone is insufficient

## Next Blocker

m1356-paper-route-materialized-source-history-pair-group-update-branch-synthesis
