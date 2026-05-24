# m579-bc-family-moderate-ood-repeat-eval Research Review

## Summary

- Generated at UTC: 20260524T063030Z
- Type: gate
- Gate tier: generalization
- Promotion decision: bc_family_ood_repeat_pass_admit_m580_audit
- Decision reason: M579 moderate-OOD family repeat passes all three BC seeds; selected BC5660 is slightly above L2 on success collision return and margin

## Hypothesis

Because all three scaled BC seeds passed the fresh route repeat, at least two should remain L0-safe and OOD-L2-competitive on a fresh moderate-OOD route repeat.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m578_bc_family_fresh_route_repeat_eval/summary.json, runs/m575_moderate_ood_route_generalization_eval/summary.json
- parent_config: configs/eval_m574_moderate_ood_l0.json, configs/eval_m574_moderate_ood_l2.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: moderate-OOD route repeat for BC seed family
- derived_from: m578-bc-family-fresh-route-repeat-eval
- blocked_by: m578-bc-family-fresh-route-repeat-eval
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 completes with episodes=256 and seed_list 22560..22815
- summary reports uses_public_frozen_source_rows=false
- BC5660 passes the L0 gate and OOD-L2 competitiveness tolerances
- at least two of three BC seeds pass L0 and OOD-L2 competitiveness tolerances
- collision deltas against L2 are computed for all BC candidates
- research validation passes

## Failure Criteria

- BC5660 fails the OOD repeat
- fewer than two BC seeds pass the OOD repeat
- evaluation reuses old route seeds or public frozen-source rows
- checkpoint promotion is attempted

## Evidence Gates

- run route-screen v2 for L0 L2 and BC5660/5661/5662 on fresh OOD seeds 22560..22815
- verify uses_public_frozen_source_rows is false
- verify BC5660 remains L0-safe and OOD-L2-competitive
- verify at least two of three BC seeds are L0-safe and OOD-L2-competitive
- do not promote checkpoint from this repeat gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reuse route seed starts 15560 16560 17560 18560 19560 20560 or 21560
- do not use public frozen-source natural-surface rows
- do not tune BC candidates before reporting M579
- do not run PPO or behavior cloning
- do not change checkpoint weights or actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m579-bc-family-moderate-ood-repeat-eval
- type: gate
- checkpoint: runs/m579_bc_family_moderate_ood_repeat_eval/summary.json
- success_rate: 0.582031
- termination_rate: 0.417969
- clearance_margin_mean: 0.921253
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_family_ood_repeat_pass_admit_m580_audit
- reason: M579 moderate-OOD family repeat passes all three BC seeds; selected BC5660 is slightly above L2 on success collision return and margin

## Next Blocker

m580-bc-family-generalization-audit
