# m571-fresh-route-generalization-design Research Review

## Summary

- Generated at UTC: 20260524T060701Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: fresh_route_generalization_design_admit_m572_eval
- Decision reason: M571 pre-registers a fresh 256-episode route/generalization gate with seed range 19560..19815 and no PPO promotion or public-row tuning

## Hypothesis

Because BC5660 passed route-screen v2 and matched L2 on public natural surfaces, the next reliable evidence layer should be a pre-registered fresh route/generalization gate rather than another public-surface iteration.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json, runs/m569_scaled_bc_route_screen_selection/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: design fresh route/generalization evidence after scaled BC public diagnostic pass
- derived_from: m570-scaled-bc-public-natural-surface-eval
- blocked_by: m570-scaled-bc-public-natural-surface-eval
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies fresh evaluation seeds and excludes prior route-screen seeds
- design specifies route/generalization randomization axes and scenario count
- design specifies BC5660 versus L0/L2 pass/fail criteria before evaluation
- design states that no promotion or PPO is allowed in M571
- research validation passes

## Failure Criteria

- design reuses public frozen-source rows as fresh evidence
- design reuses prior route-screen seeds for generalization claims
- design changes actor inputs or allows L2 stack leakage into L3 deployment
- design allows promotion before fresh evaluation results exist

## Evidence Gates

- design fresh non-public route/generalization scenario seeds for BC5660 versus L0/L2
- define OOD/randomization profile across speed friction obstacle timing road geometry and actuator lag
- define pass/fail criteria before running evaluation
- keep public frozen-source natural surfaces out of tuning and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route-screen seeds 15560 16560 17560 or 18560
- do not tune from M543 M550 M565 or M570 public frozen-source residuals
- do not run PPO or behavior cloning in this design milestone
- do not promote BC5660 from M570 public diagnostics
- do not change the P0 human-view no-wheel no-oracle actor contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m571-fresh-route-generalization-design
- type: infrastructure
- checkpoint: docs/m571-fresh-route-generalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fresh_route_generalization_design_admit_m572_eval
- reason: M571 pre-registers a fresh 256-episode route/generalization gate with seed range 19560..19815 and no PPO promotion or public-row tuning

## Next Blocker

m572-fresh-route-generalization-eval
