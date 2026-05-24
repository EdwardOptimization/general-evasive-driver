# m578-bc-family-fresh-route-repeat-eval Research Review

## Summary

- Generated at UTC: 20260524T062727Z
- Type: gate
- Gate tier: generalization
- Promotion decision: bc_family_fresh_route_repeat_pass_admit_m579_ood_repeat
- Decision reason: M578 fresh route family repeat passes all three BC seeds; selected BC5660 is slightly above L2 on success collision return and margin

## Hypothesis

Because BC5660 passed public fresh-route and OOD diagnostics, at least two of the three scaled BC seeds should remain L0-safe and L2-competitive on a fresh same-distribution route repeat.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m575_moderate_ood_route_generalization_eval/summary.json, runs/m572_fresh_route_generalization_eval/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: fresh same-distribution route repeat for BC seed family
- derived_from: m577-bc-family-generalization-repeat-design
- blocked_by: m577-bc-family-generalization-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 completes with episodes=256 and seed_list 21560..21815
- summary reports uses_public_frozen_source_rows=false
- BC5660 passes the L0 gate and L2 competitiveness tolerances
- at least two of three BC seeds pass L0 and L2 competitiveness tolerances
- collision deltas against L2 are computed for all BC candidates
- research validation passes

## Failure Criteria

- BC5660 fails the repeat
- fewer than two BC seeds pass the repeat
- evaluation reuses old route seeds or public frozen-source rows
- checkpoint promotion is attempted

## Evidence Gates

- run route-screen v2 for L0 L2 and BC5660/5661/5662 on fresh route seeds 21560..21815
- verify uses_public_frozen_source_rows is false
- verify BC5660 remains L0-safe and L2-competitive
- verify at least two of three BC seeds are L0-safe and L2-competitive
- do not promote checkpoint from this repeat gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route seed starts 15560 16560 17560 18560 19560 or 20560
- do not use public frozen-source natural-surface rows
- do not tune BC candidates before reporting M578
- do not run PPO or behavior cloning
- do not change checkpoint weights or actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m578-bc-family-fresh-route-repeat-eval
- type: gate
- checkpoint: runs/m578_bc_family_fresh_route_repeat_eval/summary.json
- success_rate: 0.675781
- termination_rate: 0.324219
- clearance_margin_mean: 0.992939
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_family_fresh_route_repeat_pass_admit_m579_ood_repeat
- reason: M578 fresh route family repeat passes all three BC seeds; selected BC5660 is slightly above L2 on success collision return and margin

## Next Blocker

m579-bc-family-moderate-ood-repeat-eval
