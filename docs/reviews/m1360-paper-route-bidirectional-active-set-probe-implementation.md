# m1360-paper-route-bidirectional-active-set-probe-implementation Research Review

## Summary

- Generated at UTC: 20260528T203015Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bidirectional_active_set_probe_m267_margin_gap_washout_route_to_result_audit
- Decision reason: M1360 exact metrics beat M1355 and preserve M267 success-drop count but fail M267 margin-gap retention by 0.0012517729

## Hypothesis

The M1358 combined anchor can reduce the M1355 wrong-branch proof washout while still improving exact source-history metrics in one bounded no-PPO update.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1359-paper-route-bidirectional-active-set-probe-design.md, runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz, runs/m1336_materialized_source_history_objective_corpus_export
- parent_config: experiments/manifests/m1359-paper-route-bidirectional-active-set-probe-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run exactly one no-PPO bidirectional active-set probe using the M1358 combined anchor
- derived_from: m1359-paper-route-bidirectional-active-set-probe-design
- blocked_by: M1359 designs the probe but no implementation has been run
- supersedes: direct PPO after M1359, direct promotion after anchor export, normal-only retention coefficient tuning
- invalidates: None

## Success Criteria

- runs/m1360_bidirectional_active_set_probe/summary.json exists
- summary records use of runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
- summary records mutation scope and actor input contract checks
- summary records exact source-history metrics versus M1154 and M1355
- summary records M267/M264 and conditional M183/M170 replay outcomes
- no PPO, promotion, private holdout, threshold relaxation, full replay, or actor-input expansion occurs

## Failure Criteria

- summary artifact is missing
- M1358 combined anchor is not used
- mutation or actor contract checks are missing
- exact metrics are missing
- M267/M264 is skipped before M183/M170
- PPO, private holdout, promotion, threshold relaxation, full replay, or actor-input expansion occurs

## Evidence Gates

- M1360 must not run PPO
- M1360 must not use private holdout
- M1360 must not promote
- M1360 must preserve actor input contract
- M1360 must use the M1358 combined anchor
- M1360 must verify mutation scope
- M1360 must evaluate exact source-history metrics before replay
- M1360 must run M267/M264 before M183/M170

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

- proof_washout

## Scoreboard

- milestone: m1360-paper-route-bidirectional-active-set-probe-implementation
- type: infrastructure
- checkpoint: runs/m1360_bidirectional_active_set_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_active_set_probe_m267_margin_gap_washout_route_to_result_audit
- reason: M1360 exact metrics beat M1355 and preserve M267 success-drop count but fail M267 margin-gap retention by 0.0012517729

## Next Blocker

m1361-paper-route-bidirectional-active-set-probe-result-audit
