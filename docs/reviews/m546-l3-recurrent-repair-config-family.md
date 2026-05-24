# m546-l3-recurrent-repair-config-family Research Review

## Summary

- Generated at UTC: 20260524T040608Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l3_repair_config_family_pass_admit_m547_route_pilot
- Decision reason: M546 adds fast-select lr1e4 and lr5e5 L3-only repair configs while preserving the M541 L3 environment and P0 contract

## Hypothesis

Controlled L3 repair configs can test whether checkpoint selection and lower recurrent update aggressiveness fix the M544 instability without changing the P0 input contract or task distribution.

## Lineage

- parent_checkpoint: runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m545-l3-recurrent-recipe-repair-design.md, runs/m544_l3_variance_recipe_failure_audit/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: implement controlled L3 recurrent repair configs after M545 design
- derived_from: m545-l3-recurrent-recipe-repair-design
- blocked_by: m545-l3-recurrent-recipe-repair-design
- supersedes: None
- invalidates: None

## Success Criteria

- repair configs are added for fast-select, lr1e4, and lr5e5 variants
- each repair config keeps the M541 L3 environment and P0 history-baseline metadata
- tests cover approved config differences and reject hidden task-distribution changes
- research validation passes

## Failure Criteria

- configs change actor input contract, reward, or environment distribution
- configs allow public-row checkpoint selection
- tests do not distinguish allowed repair controls from hidden tuning

## Evidence Gates

- add L3-only repair configs with pre-registered checkpoint interval and lower-LR variants
- tests verify the P0 input contract and unchanged environment distribution
- tests verify allowed differences from M541 L3 are limited to optimization/checkpoint-selection controls
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not modify L3 actor inputs
- do not change environment sampler ranges or reward terms
- do not run repaired training before the config family is tested
- do not claim L3 beats L2 from an L3-only repair branch

## Failure Taxonomy

- none

## Scoreboard

- milestone: m546-l3-recurrent-repair-config-family
- type: infrastructure
- checkpoint: configs/ppo_m546_l3_repair_fast_select_4096.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_repair_config_family_pass_admit_m547_route_pilot
- reason: M546 adds fast-select lr1e4 and lr5e5 L3-only repair configs while preserving the M541 L3 environment and P0 contract

## Next Blocker

m547-l3-recurrent-repair-route-pilot
