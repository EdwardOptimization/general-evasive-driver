# m1359-paper-route-bidirectional-active-set-probe-design Research Review

## Summary

- Generated at UTC: 20260528T201841Z
- Type: gate
- Gate tier: process
- Promotion decision: bidirectional_active_set_probe_design_admit_implementation
- Decision reason: M1359 designs a no-PPO combined-anchor probe with exact-first M267-first evaluation before any PPO or promotion

## Hypothesis

A no-PPO bidirectional active-set probe can be specified to consume the M1358 combined anchor and test exact source-history improvement without sacrificing correct-history or wrong-history replay behavior.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1358-paper-route-bidirectional-active-set-anchor-export.md, runs/m1358_bidirectional_active_set_anchor_export/summary.json, runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz, runs/m1336_materialized_source_history_objective_corpus_export
- parent_config: experiments/manifests/m1358-paper-route-bidirectional-active-set-anchor-export.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design a no-PPO probe that combines source-history pair-group objective with the M1358 bidirectional trajectory anchor
- derived_from: m1358-paper-route-bidirectional-active-set-anchor-export
- blocked_by: M1358 exports the combined anchor but no update protocol has been specified
- supersedes: direct PPO after M1358, direct actor update without a pre-registered bidirectional probe design, more normal-only retention coefficient tuning
- invalidates: None

## Success Criteria

- docs/m1359-paper-route-bidirectional-active-set-probe-design.md exists
- design consumes runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
- design specifies trainable scope and mutation checks
- design specifies exact source-history metrics before replay
- design specifies M267/M264 before M183/M170
- design routes to exactly one no-PPO implementation probe
- no training, PPO, replay, promotion, private holdout, threshold relaxation, actor update, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits combined-anchor consumption
- design omits wrong-history branch constraints
- design omits exact-first or M267-first order
- design routes directly to PPO or promotion
- training, PPO, replay, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Evidence Gates

- M1359 must not train
- M1359 must not run PPO
- M1359 must not run replay
- M1359 must not update actor weights
- M1359 must not use private holdout
- M1359 must not promote
- M1359 must preserve actor input contract
- M1359 must specify exact-first and M267-first evaluation order

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
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

- milestone: m1359-paper-route-bidirectional-active-set-probe-design
- type: gate
- checkpoint: docs/m1359-paper-route-bidirectional-active-set-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_active_set_probe_design_admit_implementation
- reason: M1359 designs a no-PPO combined-anchor probe with exact-first M267-first evaluation before any PPO or promotion

## Next Blocker

m1360-paper-route-bidirectional-active-set-probe-implementation
