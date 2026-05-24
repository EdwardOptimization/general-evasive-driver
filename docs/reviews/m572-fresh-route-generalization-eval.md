# m572-fresh-route-generalization-eval Research Review

## Summary

- Generated at UTC: 20260524T060945Z
- Type: gate
- Gate tier: generalization
- Promotion decision: fresh_route_generalization_pass_admit_m573_ood_design
- Decision reason: M572 fresh 256-episode route eval shows BC5660 passes L0 gate and slightly beats L2 on success collision and mean margin; no checkpoint promotion

## Hypothesis

Because BC5660 matches L2 on public natural surfaces and passed fresh route-screen selection, it should remain L2-competitive on a larger fresh non-public route/generalization seed range.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json, runs/m569_scaled_bc_route_screen_selection/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: fresh non-public route/generalization eval after M571 design
- derived_from: m571-fresh-route-generalization-design
- blocked_by: m571-fresh-route-generalization-design
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 completes with episodes=256 and seed_list 19560..19815
- summary reports uses_public_frozen_source_rows=false
- BC5660 passes the L0 success margin and collision tolerance gate
- BC5660 satisfies L2 competitiveness tolerances: success within 0.02 margin within 0.05 collision within 0.02
- research validation passes

## Failure Criteria

- evaluation reuses old route-screen seeds or public frozen-source rows
- BC5660 falls below L0 on route-screen v2 gates
- BC5660 is not L2-competitive under pre-registered tolerances
- metadata or actor contract changes
- checkpoint promotion is attempted

## Evidence Gates

- run route-screen v2 for L0 L2 and BC5660 on fresh seed range 19560..19815
- verify uses_public_frozen_source_rows is false
- verify BC5660 passes L0 success margin and collision tolerance
- verify BC5660 remains L2-competitive on success margin and collision
- do not promote checkpoint from this single fresh route gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route-screen seeds 15560 16560 17560 or 18560
- do not use public frozen-source natural-surface rows
- do not tune BC5660 from this evaluation before reporting M572
- do not run PPO or behavior cloning in M572
- do not change the P0 human-view no-wheel no-oracle actor contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m572-fresh-route-generalization-eval
- type: gate
- checkpoint: runs/m572_fresh_route_generalization_eval/summary.json
- success_rate: 0.625000
- termination_rate: 0.375000
- clearance_margin_mean: 1.064947
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fresh_route_generalization_pass_admit_m573_ood_design
- reason: M572 fresh 256-episode route eval shows BC5660 passes L0 gate and slightly beats L2 on success collision and mean margin; no checkpoint promotion

## Next Blocker

m573-moderate-ood-route-generalization-design
