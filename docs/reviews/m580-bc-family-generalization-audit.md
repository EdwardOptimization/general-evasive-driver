# m580-bc-family-generalization-audit Research Review

## Summary

- Generated at UTC: 20260524T063406Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_family_generalization_audit_admit_recurrent_ablation_design
- Decision reason: M580 audits positive BC family route/OOD evidence and admits recurrent-dependence ablation design before promotion or PPO

## Hypothesis

Because the scaled BC family now passes fresh-route and moderate-OOD repeats, the next evidence layer should test recurrent command-response dependence before promotion or PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m568_scaled_l3_bc_seed5661/checkpoint.pt, runs/m568_scaled_l3_bc_seed5662/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m578_bc_family_fresh_route_repeat_eval/summary.json, runs/m579_bc_family_moderate_ood_repeat_eval/summary.json, runs/m575_moderate_ood_route_generalization_eval/summary.json, runs/m572_fresh_route_generalization_eval/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: audit BC family route and OOD repeat evidence before recurrent-dependence gates
- derived_from: m579-bc-family-moderate-ood-repeat-eval
- blocked_by: m579-bc-family-moderate-ood-repeat-eval
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes M578 and M579 family metrics
- audit identifies remaining proof gaps
- audit pre-registers next recurrent-dependence gate direction
- research validation passes

## Failure Criteria

- audit treats family route/OOD metrics as sufficient for promotion
- audit skips recurrent-dependence evidence
- audit allows PPO before proof gaps are addressed

## Evidence Gates

- audit BC family fresh-route and OOD repeat evidence
- identify remaining evidence gaps before promotion
- decide recurrent-dependence ablation/proof gate sequence
- do not train evaluate or promote in audit milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from route/OOD family metrics alone
- do not run PPO or behavior cloning
- do not change actor inputs
- do not skip recurrent-dependence diagnostics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m580-bc-family-generalization-audit
- type: gate
- checkpoint: docs/m580-bc-family-generalization-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_family_generalization_audit_admit_recurrent_ablation_design
- reason: M580 audits positive BC family route/OOD evidence and admits recurrent-dependence ablation design before promotion or PPO

## Next Blocker

m581-bc-recurrent-ablation-design
