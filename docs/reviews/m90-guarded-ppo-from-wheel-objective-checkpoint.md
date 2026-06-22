# m90-guarded-ppo-from-wheel-objective-checkpoint Research Review

## Summary

- Generated at UTC: 20260621T080721Z
- Type: driver_candidate
- Gate tier: legacy
- Promotion decision: manual_review
- Decision reason: Accept as a continuation candidate only if aggregate success is at least 0.85, zero-wheel success is at least 0.10 below normal success, reset is not better than normal, and mu body+wheel gain remains at least 0.10. Otherwise reject and move to matched wrong-wheel-history corpus.

## Hypothesis

Guarded PPO continuation from the M89 objective-only wheel-aware checkpoint can preserve driving behavior while increasing causal dependence on wheel response.

## Lineage

- parent_checkpoint: None
- parent_dataset: None
- parent_config: None
- parent_objective: None
- derived_from: None
- blocked_by: None
- supersedes: None
- invalidates: None

## Success Criteria

- normal success_rate >= 0.85 on the 20-episode same-seed gate
- normal success_rate - zero_wheel_success >= 0.10
- reset_success <= normal success_rate
- mu_bucket body_plus_wheel_gain >= 0.10
- no hidden parameters or oracle labels are added to actor observations

## Failure Criteria

- normal success_rate < 0.85
- normal success_rate - zero_wheel_success < 0.10
- wheel_gain_mu < 0.10
- clearance margin regresses below the M89 same-seed gate
- training fails to produce checkpoint and gate artifacts

## Evidence Gates

- None recorded.

## Holdout Policy

- legacy

## Forbidden Shortcuts

- None recorded.

## Failure Taxonomy

- None recorded.

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

None recorded.
