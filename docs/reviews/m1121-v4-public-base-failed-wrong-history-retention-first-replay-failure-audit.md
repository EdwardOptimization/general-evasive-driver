# m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit Research Review

## Summary

- Generated at UTC: 20260527T212458Z
- Type: gate
- Gate tier: process
- Promotion decision: failed_wrong_history_retention_failure_audit_route_to_row15_unsafe_margin_retention_design
- Decision reason: M1121 finds row15 pair 9530:21:9550:21 was covered by 170 target-base trajectory anchor rows but low action MSE still allowed wrong-history terminal margin crossing so the next repair must target unsafe margin directly

## Hypothesis

M1120 failed because row15's wrong-history terminal margin crosses zero despite low trajectory-action-anchor MSE, so the next repair must target terminal or unsafe-margin retention rather than more generic action anchoring.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- parent_dataset: runs/m1120_failed_wrong_history_retention_first_replay/summary.json, runs/m1120_failed_wrong_history_retention_first_replay/first_replay_summary.csv, runs/m1120_failed_wrong_history_retention_first_replay/lost_success_drop_rows.csv, runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.csv, runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz
- parent_config: experiments/manifests/m1120-v4-public-base-failed-wrong-history-retention-first-replay-run.json
- parent_objective: audit why the M1118 retention-aware candidate still makes row15 wrong-history rollouts safe
- derived_from: m1120-v4-public-base-failed-wrong-history-retention-first-replay-run
- blocked_by: M1120 rejects m1118_seed111800 first replay through wrong-history-safe row15
- supersedes: None
- invalidates: family-intersection replay before row15 audit, full public gate before row15 audit, PPO from m1118_seed111800, promotion of m1118_seed111800

## Success Criteria

- audit artifact exists
- row15 anchor coverage in M1115 is classified
- row15 target-base trajectory MSE versus terminal-margin crossing is classified
- next repair route is explicit
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- audit artifact is missing
- row15 coverage remains ambiguous
- next route is ambiguous
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1121 must audit existing M1115 and M1120 artifacts only
- M1121 must not train actor weights
- M1121 must not run PPO
- M1121 must not run replay
- M1121 must not mine new rows
- M1121 must not promote
- M1121 must not use private holdout
- M1121 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not continue to family-intersection replay before audit
- do not weaken replay thresholds

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit
- type: gate
- checkpoint: docs/m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: failed_wrong_history_retention_failure_audit_route_to_row15_unsafe_margin_retention_design
- reason: M1121 finds row15 pair 9530:21:9550:21 was covered by 170 target-base trajectory anchor rows but low action MSE still allowed wrong-history terminal margin crossing so the next repair must target unsafe margin directly

## Next Blocker

m1122-v4-public-base-row15-unsafe-margin-retention-design
