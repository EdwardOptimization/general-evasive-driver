# m432-selective-10004-guard-design Research Review

## Summary

- Generated at UTC: 20260523T181056Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m433_selective_10004_anchor_export
- Decision reason: M432 designs selective 10004 wrong-history radius profiles while keeping 10023 and 9872 guards unchanged

## Hypothesis

The M430 utility collapse can be relieved by treating 10004 wrong-history as a selective branch guard rather than a tiny-radius all-hard full-trajectory anchor, while keeping 10023 and 9872 proof guards intact.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m427_projected_recovery_ltraj1e13_s40_seed10156/candidate_checkpoint.pt, runs/m430_branch_split_projected_ltraj1e13_s40_seed10157/candidate_checkpoint.pt
- parent_dataset: runs/m429_branch_split_old_key_guard/branch_split_hard_guard_anchor.npz, runs/m431_branch_split_utility_balance_audit/branch_split_source_summary.csv
- parent_config: experiments/manifests/m431-branch-split-utility-balance-audit.json
- parent_objective: selective branch-specific guard design for 10004 wrong-history
- derived_from: m431-branch-split-utility-balance-audit
- blocked_by: m431-branch-split-utility-balance-audit
- supersedes: None
- invalidates: None

## Success Criteria

- specify a selective 10004 guard profile or exporter change
- keep 10023 wrong-history and 9872 normal guards hard in the first probe
- pre-register a no-PPO projection probe with recovery retained vs M406 >= 0.20 as primary utility target
- retain M427 recovery utility 0.174354 as the minimum useful comparison

## Failure Criteria

- design requires lowering proof gates
- design removes 10004 wrong-history protection entirely
- design changes actor input/output contract
- design recommends PPO before a no-PPO selective proof probe

## Evidence Gates

- design only; no PPO
- next probe must keep exact M297/M270/old-key no-regression
- next probe must keep M267/M264 17/17 old-key compact 40/40 and M183/M170 17/17
- next probe must evaluate recovery retained vs M406

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower replay or exact thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m432-selective-10004-guard-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m433_selective_10004_anchor_export
- reason: M432 designs selective 10004 wrong-history radius profiles while keeping 10023 and 9872 guards unchanged

## Next Blocker

m433-selective-10004-anchor-export
