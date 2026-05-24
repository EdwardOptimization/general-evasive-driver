# m581-bc-recurrent-ablation-design Research Review

## Summary

- Generated at UTC: 20260524T063759Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_recurrent_ablation_design_admit_m582_fresh_route_eval
- Decision reason: M581 pre-registers BC5660 recurrent ablation diagnostics with reset zero-current zero-action and zero-all controls before evaluation

## Hypothesis

Because the scaled BC family transfers L2 behavior reliably, the next diagnostic should test whether the deployed L3 actor depends on recurrent command-response history.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt
- parent_dataset: runs/m578_bc_family_fresh_route_repeat_eval/summary.json, runs/m579_bc_family_moderate_ood_repeat_eval/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design recurrent-dependence ablation diagnostics after BC family route/OOD pass
- derived_from: m580-bc-family-generalization-audit
- blocked_by: m580-bc-family-generalization-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies ablation policies and seed blocks
- design specifies benchmark commands using existing checkpoint ablation support
- design specifies diagnostic degradation thresholds and interpretation rules
- research validation passes

## Failure Criteria

- design treats ablations as promotion by themselves
- design skips no-degradation interpretation
- design changes checkpoint weights or actor inputs
- design uses public frozen-source rows

## Evidence Gates

- design BC5660 normal vs reset/zero-current/zero-action ablation benchmarks
- define same-distribution and moderate-OOD fresh seed blocks
- pre-register diagnostic degradation thresholds
- do not train evaluate or promote in design milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim self-identification from route/OOD metrics alone
- do not run PPO or behavior cloning
- do not change actor inputs
- do not promote before recurrent-dependence diagnostics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m581-bc-recurrent-ablation-design
- type: infrastructure
- checkpoint: docs/m581-bc-recurrent-ablation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_recurrent_ablation_design_admit_m582_fresh_route_eval
- reason: M581 pre-registers BC5660 recurrent ablation diagnostics with reset zero-current zero-action and zero-all controls before evaluation

## Next Blocker

m582-bc5660-recurrent-ablation-fresh-route-eval
