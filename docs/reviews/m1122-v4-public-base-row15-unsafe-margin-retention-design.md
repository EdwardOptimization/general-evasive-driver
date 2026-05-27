# m1122-v4-public-base-row15-unsafe-margin-retention-design Research Review

## Summary

- Generated at UTC: 20260527T212858Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_unsafe_margin_retention_design_admit_projection_probe
- Decision reason: M1122 designs a no-training row15 unsafe-margin projection probe with nonzero interpolation alpha direct wrong-history terminal-margin acceptance and unchanged first-replay thresholds

## Hypothesis

A row15-specific unsafe-margin or terminal-margin retention objective can target the remaining wrong-history-safe failure more directly than increasing generic trajectory-action anchor pressure.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- parent_dataset: docs/m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit.md, runs/m1120_failed_wrong_history_retention_first_replay/lost_success_drop_rows.csv, runs/m1115_materialized_failed_wrong_history_retention_export/target_base_rejected_trajectory_anchor.csv
- parent_config: experiments/manifests/m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit.json
- parent_objective: design a row15 unsafe-margin retention objective before any further update
- derived_from: m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit
- blocked_by: M1121 classifies the M1120 failure as row15 wrong-history terminal-margin crossing despite anchor coverage
- supersedes: None
- invalidates: generic trajectory-anchor pressure increase without terminal-margin objective, family-intersection replay before row15 repair design, PPO from m1118_seed111800, promotion of m1118_seed111800

## Success Criteria

- design artifact exists
- objective terms distinguish normal-history safety from wrong-history unsafe-margin retention
- pre-replay exact and anchor gates are specified
- first replay thresholds remain unchanged
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- objective relies on deploy-time privileged actor inputs
- objective relies only on generic action MSE
- next route is ambiguous
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1122 must be design-only
- M1122 must not train actor weights
- M1122 must not run PPO
- M1122 must not run replay
- M1122 must not mine new rows
- M1122 must not promote
- M1122 must not use private holdout
- M1122 must preserve actor inputs

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
- do not weaken replay thresholds
- do not rely on action MSE alone for row15

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1122-v4-public-base-row15-unsafe-margin-retention-design
- type: gate
- checkpoint: docs/m1122-v4-public-base-row15-unsafe-margin-retention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_unsafe_margin_retention_design_admit_projection_probe
- reason: M1122 designs a no-training row15 unsafe-margin projection probe with nonzero interpolation alpha direct wrong-history terminal-margin acceptance and unchanged first-replay thresholds

## Next Blocker

m1123-v4-public-base-row15-unsafe-margin-projection-probe
