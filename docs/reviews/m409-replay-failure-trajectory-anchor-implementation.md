# m409-replay-failure-trajectory-anchor-implementation Research Review

## Summary

- Generated at UTC: 20260523T160438Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m410_old_key_replay_failure_anchor_implementation
- Decision reason: M409 adds optional trajectory-anchor loss to exact repair and exports 669 M267/M264 replay-failure trajectory rows; old-key exporter remains next

## Hypothesis

A training-only replay-failure trajectory anchor can be exported from M407 failed rows and wired into exact_post_ppo_repair without changing the actor contract.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m407_projection_replay_failure_row_audit/m267_m264_wrong_history_washout_rows.csv, runs/m407_projection_replay_failure_row_audit/old_key_accepted_regression_rows.csv
- parent_config: experiments/manifests/m408-replay-aware-projection-residual-design.json
- parent_objective: implement training-only replay-failure trajectory anchors for exact projection
- derived_from: m408-replay-aware-projection-residual-design
- blocked_by: m408-replay-aware-projection-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- export trajectory anchor rows for M407 M267/M264 wrong-history washout rows
- handle or explicitly defer old-key failed-row trajectory export
- add optional exact_post_ppo_repair trajectory-anchor loading and loss terms
- run no-update smoke with finite trajectory anchor loss
- run focused tests and research validation

## Failure Criteria

- anchor cannot be exported from M407 rows
- exact repair cannot load the anchor
- actor input or output contract changes
- research validation fails

## Evidence Gates

- infrastructure smoke only
- no PPO run
- no checkpoint promotion
- no actor input/output change
- trajectory anchor loads in exact_post_ppo_repair no-update smoke

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m409-replay-failure-trajectory-anchor-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m410_old_key_replay_failure_anchor_implementation
- reason: M409 adds optional trajectory-anchor loss to exact repair and exports 669 M267/M264 replay-failure trajectory rows; old-key exporter remains next

## Next Blocker

m410-old-key-replay-failure-anchor-implementation
