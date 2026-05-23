# m413-replay-recovery-balance-design Research Review

## Summary

- Generated at UTC: 20260523T163041Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m414_source_weighted_replay_anchor_probe
- Decision reason: M413 designs a no-code source-weighted replay anchor probe with M267 effective lambda 1e12 old-key effective lambda 1e13 and recovery-retention ratio gate >=0.20

## Hypothesis

A more selective replay/recovery balance can preserve M411 proof gates without collapsing the candidate back to M400 behavior.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt
- parent_dataset: runs/m412_replay_aware_projection_utility_audit/summary.json, runs/m412_replay_aware_projection_utility_audit/policy_surface_metrics.csv
- parent_config: experiments/manifests/m412-replay-aware-projection-utility-audit.json
- parent_objective: redesign replay/recovery residual balance after retention-heavy projection
- derived_from: m412-replay-aware-projection-utility-audit
- blocked_by: m412-replay-aware-projection-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define active-set replay residuals that only push rows or branches near replay failure
- define recovery-preservation terms that retain M406 movement where replay gates are not threatened
- define a measurable Pareto acceptance rule for replay retention versus recovery utility
- pre-register the next no-PPO implementation or probe milestone

## Failure Criteria

- design relies on actor-input shortcuts
- design treats scalar replay-anchor collapse as sufficient progress
- design weakens exact or replay gates
- design cannot be tested without PPO

## Evidence Gates

- design only
- no PPO run
- no checkpoint promotion
- no actor input/output change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not count replay-anchor collapse as driver progress

## Failure Taxonomy

- none

## Scoreboard

- milestone: m413-replay-recovery-balance-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m414_source_weighted_replay_anchor_probe
- reason: M413 designs a no-code source-weighted replay anchor probe with M267 effective lambda 1e12 old-key effective lambda 1e13 and recovery-retention ratio gate >=0.20

## Next Blocker

m414-source-weighted-replay-anchor-probe
