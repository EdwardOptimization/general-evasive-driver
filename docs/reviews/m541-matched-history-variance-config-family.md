# m541-matched-history-variance-config-family Research Review

## Summary

- Generated at UTC: 20260524T034332Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: matched_variance_config_family_pass_admit_m542_route_pilot
- Decision reason: M541 adds machine-checkable matched 4096-step L0 L2 L3 configs and fairness tests without training

## Hypothesis

A machine-checkable 4096-step matched config family can be added so the next variance run compares L0 L2 and L3 fairly after the M539 seed-fragility finding.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m540-matched-history-training-variance-design.md
- parent_config: configs/ppo_m531_matched_l0_short_train.json, configs/ppo_m531_matched_l2_short_train.json, configs/ppo_m531_matched_l3_short_train.json
- parent_objective: implement matched 4096-step L0 L2 L3 variance config family
- derived_from: m540-matched-history-training-variance-design
- blocked_by: m540-matched-history-training-variance-design
- supersedes: None
- invalidates: None

## Success Criteria

- three configs exist for L0 L2 and L3
- only actor encoder history length recurrent flag and history baseline metadata differ by level
- shared PPO budget and environment task distribution are tested
- research validation passes

## Failure Criteria

- configs differ in unapproved per-level ways
- P0 input contract changes
- training or promotion is performed

## Evidence Gates

- added matched 4096-step L0 L2 L3 configs
- tested shared budget and approved history-level differences
- preserved P0 input contract
- did not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change task distribution for one history level only
- do not run training before config tests pass
- do not tune L3 against public M537-M539 rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m541-matched-history-variance-config-family
- type: infrastructure
- checkpoint: configs/ppo_m541_matched_l3_variance_4096.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: matched_variance_config_family_pass_admit_m542_route_pilot
- reason: M541 adds machine-checkable matched 4096-step L0 L2 L3 configs and fairness tests without training

## Next Blocker

m542-matched-history-variance-route-pilot
