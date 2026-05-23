# m408-replay-aware-projection-residual-design Research Review

## Summary

- Generated at UTC: 20260523T155857Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m409_replay_failure_trajectory_anchor_implementation
- Decision reason: M408 designs branch-specific replay-failure trajectory anchors as training-only projection residuals while keeping exact feasibility and closed-loop replay gates authoritative

## Hypothesis

Because M406 exact feasibility still failed closed-loop replay broadly, the next repair needs a training-only replay-aware or short-trajectory residual built from failed public proof rows, while keeping replay gates authoritative.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
- parent_dataset: runs/m407_projection_replay_failure_row_audit/summary.json, runs/m407_projection_replay_failure_row_audit/m267_m264_wrong_history_washout_rows.csv, runs/m407_projection_replay_failure_row_audit/old_key_accepted_regression_rows.csv
- parent_config: experiments/manifests/m407-m406-projection-replay-failure-row-audit.json
- parent_objective: design a replay-aware projection residual after exact-feasible closed-loop replay failure
- derived_from: m407-m406-projection-replay-failure-row-audit
- blocked_by: m407-m406-projection-replay-failure-row-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define which M407 rows become training-only replay-aware residual inputs
- define whether residual targets are one-step rejected actions, short trajectory anchors, or terminal-margin sign constraints
- define lexicographic ordering relative to exact M297/M270/old-key feasibility
- pre-register an implementation milestone without changing actor inputs

## Failure Criteria

- design leaks replay labels or oracle outcomes into actor inputs
- design treats the replay-aware residual as a replacement for closed-loop replay gates
- design lowers thresholds
- research validation fails

## Evidence Gates

- design only
- no PPO run
- no checkpoint promotion
- preserve exact M297/M270/old-key feasibility
- use M407 failed closed-loop rows as replay-aware training-only residual candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make M267/M264 or old-key replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m408-replay-aware-projection-residual-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m409_replay_failure_trajectory_anchor_implementation
- reason: M408 designs branch-specific replay-failure trajectory anchors as training-only projection residuals while keeping exact feasibility and closed-loop replay gates authoritative

## Next Blocker

m409-replay-failure-trajectory-anchor-implementation
