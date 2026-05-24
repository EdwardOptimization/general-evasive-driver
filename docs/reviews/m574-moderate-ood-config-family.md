# m574-moderate-ood-config-family Research Review

## Summary

- Generated at UTC: 20260524T061617Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: moderate_ood_config_family_pass_admit_m575_eval
- Decision reason: M574 adds eval-only OOD L0/L2/L3 configs and tests exact parent PPO approved env deltas and route-screen loading without evaluation

## Hypothesis

Because M573 fixed the moderate-OOD profile, eval-only configs can be added with identical OOD env deltas across L0/L2/L3 while preserving each level's history contract.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m572_fresh_route_generalization_eval/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: implement eval-only moderate-OOD route configs from M573 design
- derived_from: m573-moderate-ood-route-generalization-design
- blocked_by: m573-moderate-ood-route-generalization-design
- supersedes: None
- invalidates: None

## Success Criteria

- three eval-only configs are added under configs/
- tests verify approved OOD env deltas and preserved level-specific history fields
- configs load successfully for route-screen v2
- research validation passes

## Failure Criteria

- config changes actor inputs or history contract unexpectedly
- OOD deltas differ across L0/L2/L3 except for approved history fields
- configs fail to load
- training evaluation or promotion is performed

## Evidence Gates

- add eval_m574_moderate_ood_l0/l2/l3 configs
- verify only approved env deltas and level-specific history fields differ from M541 parents
- verify configs load through route-screen env config loader
- do not run evaluation training or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or evaluate in M574
- do not change checkpoint weights
- do not change actor inputs
- do not alter L0/L2/L3 history levels beyond approved parent contracts
- do not use public frozen-source natural-surface rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m574-moderate-ood-config-family
- type: infrastructure
- checkpoint: docs/m574-moderate-ood-config-family.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: moderate_ood_config_family_pass_admit_m575_eval
- reason: M574 adds eval-only OOD L0/L2/L3 configs and tests exact parent PPO approved env deltas and route-screen loading without evaluation

## Next Blocker

m575-moderate-ood-route-generalization-eval
