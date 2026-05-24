# m577-bc-family-generalization-repeat-design Research Review

## Summary

- Generated at UTC: 20260524T062421Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_family_repeat_design_admit_m578_fresh_route_repeat
- Decision reason: M577 pre-registers BC5660/5661/5662 fresh route and moderate-OOD repeats with no promotion or PPO

## Hypothesis

Because selected BC5660 is L2-competitive on public fresh-route and moderate-OOD diagnostics, the next evidence layer should test whether the scaled BC seed family is stable before promotion or PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m575_moderate_ood_route_generalization_eval/summary.json, runs/m572_fresh_route_generalization_eval/summary.json, runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l0.json, configs/eval_m574_moderate_ood_l2.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design BC seed-family generalization repeats after M576 audit
- derived_from: m576-moderate-ood-route-eval-audit
- blocked_by: m576-moderate-ood-route-eval-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies checkpoints BC5660 BC5661 BC5662 plus L0/L2 references
- design specifies fresh same-distribution and moderate-OOD seed blocks
- design specifies family-level pass/fail criteria before evaluation
- design blocks promotion and PPO
- research validation passes

## Failure Criteria

- design evaluates or promotes before pre-registering the repeat
- design reuses old route seed starts as fresh evidence
- design ignores BC seed-family fragility risk
- design changes actor input contract or checkpoint weights

## Evidence Gates

- design fresh same-distribution repeat for BC5660 BC5661 BC5662 versus L0/L2
- design fresh moderate-OOD repeat for BC5660 BC5661 BC5662 versus L0/L2
- pre-register seed blocks pass/fail criteria and no-promotion boundary
- do not train evaluate or promote in design milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from BC5660-only evidence
- do not reuse route seed starts 15560 16560 17560 18560 19560 or 20560
- do not run PPO or behavior cloning
- do not change actor inputs or checkpoint weights
- do not use public frozen-source rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m577-bc-family-generalization-repeat-design
- type: infrastructure
- checkpoint: docs/m577-bc-family-generalization-repeat-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_family_repeat_design_admit_m578_fresh_route_repeat
- reason: M577 pre-registers BC5660/5661/5662 fresh route and moderate-OOD repeats with no promotion or PPO

## Next Blocker

m578-bc-family-fresh-route-repeat-eval
