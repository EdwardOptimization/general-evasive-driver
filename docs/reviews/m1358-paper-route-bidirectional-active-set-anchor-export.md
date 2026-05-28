# m1358-paper-route-bidirectional-active-set-anchor-export Research Review

## Summary

- Generated at UTC: 20260528T201841Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bidirectional_active_set_anchor_export_pass_route_to_probe_design
- Decision reason: M1358 exports a 12113-row combined correct-history and wrong-history anchor with rows 6 10 13 15 16 present and no actor update

## Hypothesis

The M1355 wrong-history safe rows can be materialized into a combined correct/wrong trajectory anchor for a later bidirectional active-set update.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1357-paper-route-bidirectional-replay-active-set-design.md, runs/m1355_materialized_source_history_replay_aware_retention_probe/retention_surface/retention_trajectory_anchor.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1357-paper-route-bidirectional-replay-active-set-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: export combined correct-history and wrong-history trajectory anchors for bidirectional active-set branch
- derived_from: m1357-paper-route-bidirectional-replay-active-set-design
- blocked_by: M1357 designs the bidirectional objective but the wrong-history anchor artifact has not been exported
- supersedes: direct actor update before rejected-branch anchor export
- invalidates: None

## Success Criteria

- runs/m1358_bidirectional_active_set_anchor_export/summary.json exists
- summary records required row ids 6,10,13,15,16 present
- summary records rejected trajectory rows
- summary records combined anchor rows
- summary verifies combined anchor load
- no training, PPO, promotion, private holdout, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- required row ids are missing
- combined anchor cannot load
- training, PPO, private holdout, promotion, threshold relaxation, actor update, replay run, or actor-input expansion occurs

## Evidence Gates

- M1358 must not train
- M1358 must not run PPO
- M1358 must not update actor weights
- M1358 must not use private holdout
- M1358 must not promote
- M1358 must export required wrong-history row ids 6,10,13,15,16
- M1358 must verify the combined anchor loads

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor weights
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1358-paper-route-bidirectional-active-set-anchor-export
- type: infrastructure
- checkpoint: runs/m1358_bidirectional_active_set_anchor_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_active_set_anchor_export_pass_route_to_probe_design
- reason: M1358 exports a 12113-row combined correct-history and wrong-history anchor with rows 6 10 13 15 16 present and no actor update

## Next Blocker

m1359-paper-route-bidirectional-active-set-probe-design
