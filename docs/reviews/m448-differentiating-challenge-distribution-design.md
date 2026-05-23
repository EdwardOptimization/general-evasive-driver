# m448-differentiating-challenge-distribution-design Research Review

## Summary

- Generated at UTC: 20260523T193251Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m449_challenge_distribution_config_implementation
- Decision reason: M448 designs near-threshold and late high-energy zero-relvel challenge distributions after M121 fails to separate candidates

## Hypothesis

The current M121 distribution is too insensitive to distinguish recent checkpoints, so the next step should design a more challenging near-boundary scenario distribution before more objective design.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m447_fresh_policy_difference_benchmark_seed9700/episodes.csv, runs/m447_fresh_policy_difference_mining_seed9700/policy_difference_summary.json
- parent_config: configs/m121_human_view_zero_obstacle_relvel.json, experiments/manifests/m447-fresh-policy-difference-mining-run.json
- parent_objective: differentiating challenge distribution design
- derived_from: m447-fresh-policy-difference-mining-run
- blocked_by: m447-fresh-policy-difference-mining-run
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies concrete config changes
- design specifies smoke sampling checks
- design specifies policy-difference mining gates
- design does not change actor inputs

## Failure Criteria

- design only proposes more active-boundary tuning
- design uses hidden/oracle actor inputs
- design lacks a way to test whether scenarios are more discriminative
- design promotes a checkpoint

## Evidence Gates

- design a harder fresh scenario distribution
- preserve P0 human-view no-wheel actor contract
- define smoke and mining acceptance criteria
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add hidden or oracle actor inputs
- do not use planner/reference features
- do not lower existing proof gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m448-differentiating-challenge-distribution-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m449_challenge_distribution_config_implementation
- reason: M448 designs near-threshold and late high-energy zero-relvel challenge distributions after M121 fails to separate candidates

## Next Blocker

m449-challenge-distribution-config-implementation
