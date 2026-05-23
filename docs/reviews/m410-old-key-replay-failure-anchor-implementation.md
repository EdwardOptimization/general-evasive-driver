# m410-old-key-replay-failure-anchor-implementation Research Review

## Summary

- Generated at UTC: 20260523T161431Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m411_combined_replay_aware_projection_probe
- Decision reason: M410 exports 290 old-key replay-failure trajectory rows across 7 failed rows with branch split 1 normal and 6 wrong-history; no-update exact repair smoke loads them with exact no-regression

## Hypothesis

Old-key compact replay failures need a branch-specific training-only trajectory anchor exporter before a full M409/M410 replay-aware projection probe can be fair.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m407_projection_replay_failure_row_audit/old_key_accepted_regression_rows.csv, runs/m406_a01proj_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m409_m407_m267_replay_failure_trajectory_anchor/rejected_trajectory_anchor.npz
- parent_config: experiments/manifests/m409-replay-failure-trajectory-anchor-implementation.json
- parent_objective: implement old-key-specific replay-failure trajectory anchors
- derived_from: m409-replay-failure-trajectory-anchor-implementation
- blocked_by: m409-replay-failure-trajectory-anchor-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- export wrong-history trajectory anchors for the six old-key wrong-history-safe regressions
- export or explicitly represent the one old-key normal-branch failure with a successful normal trajectory or local recovery target
- load the old-key anchor through exact_post_ppo_repair with finite trajectory loss
- run focused tests and research validation

## Failure Criteria

- old-key failed rows cannot be reconstructed
- anchor cannot be loaded by exact_post_ppo_repair
- actor input or output contract changes
- research validation fails

## Evidence Gates

- infrastructure smoke only
- no PPO run
- no checkpoint promotion
- old-key failed rows export branch-specific trajectory anchor
- trajectory anchor loads in exact_post_ppo_repair no-update smoke

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make old-key replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m410-old-key-replay-failure-anchor-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m411_combined_replay_aware_projection_probe
- reason: M410 exports 290 old-key replay-failure trajectory rows across 7 failed rows with branch split 1 normal and 6 wrong-history; no-update exact repair smoke loads them with exact no-regression

## Next Blocker

m411-combined-replay-aware-projection-probe
