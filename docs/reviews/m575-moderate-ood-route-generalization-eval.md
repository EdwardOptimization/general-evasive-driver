# m575-moderate-ood-route-generalization-eval Research Review

## Summary

- Generated at UTC: 20260524T061912Z
- Type: gate
- Gate tier: generalization
- Promotion decision: moderate_ood_route_generalization_pass_admit_m576_audit
- Decision reason: M575 moderate-OOD route eval shows BC5660 matches L2 success/collision and slightly improves return and mean margin; no checkpoint promotion

## Hypothesis

Because BC5660 passed same-distribution fresh route generalization, it should remain L0-safe and near the L2 finite-window reference on a moderate-OOD route profile.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m572_fresh_route_generalization_eval/summary.json
- parent_config: configs/eval_m574_moderate_ood_l0.json, configs/eval_m574_moderate_ood_l2.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: moderate-OOD route/generalization eval after M574 config family
- derived_from: m574-moderate-ood-config-family
- blocked_by: m574-moderate-ood-config-family
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 completes with episodes=256 and seed_list 20560..20815
- summary reports uses_public_frozen_source_rows=false
- all policies use eval_m574_moderate_ood_l0/l2/l3 configs
- BC5660 passes the L0 success margin and collision tolerance gate
- BC5660 satisfies OOD-L2 competitiveness: success within 0.05 margin within 0.10 collision within 0.05
- research validation passes

## Failure Criteria

- evaluation reuses old route-screen seeds or public frozen-source rows
- BC5660 falls below L0 on route-screen v2 gates
- BC5660 is not OOD-L2-competitive under pre-registered tolerances
- metadata or actor contract changes
- checkpoint promotion is attempted

## Evidence Gates

- run route-screen v2 for L0 L2 and BC5660 on moderate-OOD configs
- use fresh OOD seed range 20560..20815
- verify uses_public_frozen_source_rows is false
- verify BC5660 passes L0 success margin and collision tolerance
- verify BC5660 remains OOD-L2-competitive on success margin and collision
- do not promote checkpoint from this single OOD gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route-screen seed starts 15560 16560 17560 18560 or 19560
- do not use public frozen-source natural-surface rows
- do not tune BC5660 from M575 before reporting the result
- do not run PPO or behavior cloning in M575
- do not change checkpoint weights or actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m575-moderate-ood-route-generalization-eval
- type: gate
- checkpoint: runs/m575_moderate_ood_route_generalization_eval/summary.json
- success_rate: 0.628906
- termination_rate: 0.371094
- clearance_margin_mean: 1.042773
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: moderate_ood_route_generalization_pass_admit_m576_audit
- reason: M575 moderate-OOD route eval shows BC5660 matches L2 success/collision and slightly improves return and mean margin; no checkpoint promotion

## Next Blocker

m576-moderate-ood-route-eval-audit
