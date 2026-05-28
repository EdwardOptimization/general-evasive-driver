# m1357-paper-route-bidirectional-replay-active-set-design Research Review

## Summary

- Generated at UTC: 20260528T200858Z
- Type: gate
- Gate tier: process
- Promotion decision: bidirectional_replay_active_set_design_admit_anchor_export
- Decision reason: M1357 designs branch-asymmetric correct-history and wrong-history constraints and admits artifact-only anchor export for M1355 safe wrong-history rows

## Hypothesis

A bidirectional active-set design can avoid the M1355 failure by protecting both correct-history success and wrong-history rejected/failure behavior.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1355_materialized_source_history_replay_aware_retention_probe/checkpoints/raw_replay_aware_retention_update.pt
- parent_dataset: docs/m1356-paper-route-materialized-source-history-pair-group-update-branch-synthesis.md, runs/m1355_materialized_source_history_replay_aware_retention_probe/summary.json, runs/m1355_materialized_source_history_replay_aware_retention_probe/replay/m267_m264/boundary_replay_rows.csv, runs/m1352_materialized_source_history_interpolation_preflight/replay/m1352_alpha_0_005/m183_m170/boundary_replay_rows.csv, runs/m1336_materialized_source_history_objective_corpus_export
- parent_config: experiments/manifests/m1356-paper-route-materialized-source-history-pair-group-update-branch-synthesis.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design bidirectional active-set objective that protects correct-history and wrong-history branches separately
- derived_from: m1356-paper-route-materialized-source-history-pair-group-update-branch-synthesis
- blocked_by: M1356 pivots because normal-branch retention alone makes wrong-history branches successful
- supersedes: more local retention coefficient tuning, direct PPO after M1355, promotion of M1355
- invalidates: None

## Success Criteria

- docs/m1357-paper-route-bidirectional-replay-active-set-design.md exists
- design specifies correct-history branch constraints
- design specifies wrong-history branch constraints
- design identifies M1355 wrong-history safe rows as active constraints
- design specifies no-PPO implementation admission criteria
- no training, PPO, promotion, private holdout, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits wrong-history branch constraints
- design routes directly to PPO or promotion
- training, PPO, private holdout, promotion, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Evidence Gates

- M1357 must not train
- M1357 must not run PPO
- M1357 must not use private holdout
- M1357 must not promote
- M1357 must preserve actor input contract
- M1357 must design correct-history and wrong-history active-set constraints separately

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not run a new actor update
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1357-paper-route-bidirectional-replay-active-set-design
- type: gate
- checkpoint: docs/m1357-paper-route-bidirectional-replay-active-set-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_replay_active_set_design_admit_anchor_export
- reason: M1357 designs branch-asymmetric correct-history and wrong-history constraints and admits artifact-only anchor export for M1355 safe wrong-history rows

## Next Blocker

m1358-paper-route-bidirectional-active-set-anchor-export
