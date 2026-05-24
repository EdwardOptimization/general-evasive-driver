# m584-bc-recurrent-ablation-audit Research Review

## Summary

- Generated at UTC: 20260524T065435Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_recurrent_ablation_audit_admit_history_intervention_design
- Decision reason: M584 concludes M582/M583 support current-response dependence but not accumulated hidden-state self-ID; next diagnostic must directly intervene on delayed or wrong recurrent history

## Hypothesis

Because M582 and M583 show strong zero-current degradation but weak reset-hidden degradation, the next evidence layer should target causal history mismatch rather than treating current-response ablation as complete self-ID proof.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m582_bc5660_recurrent_ablation_fresh_route_eval/policy_summary.csv, runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/policy_summary.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: audit fresh-route and moderate-OOD recurrent ablation evidence before sharper self-ID gates
- derived_from: m583-bc5660-recurrent-ablation-moderate-ood-eval
- blocked_by: m583-bc5660-recurrent-ablation-moderate-ood-eval
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes M582 and M583 normal and ablation metrics
- audit classifies which evidence supports current response dependence and which does not support accumulated hidden dependence
- audit pre-registers the next diagnostic direction without promotion or PPO
- research validation passes

## Failure Criteria

- audit overclaims hidden-belief proof from zero-current degradation
- audit skips weak reset-hidden result
- audit promotes a checkpoint
- audit starts PPO before selecting the next proof gate

## Evidence Gates

- audit M582 and M583 ablation deltas side by side
- separate current-response dependence from accumulated-hidden dependence
- decide whether to broaden BC seed-family ablations or move to wrong-history/delayed-history interventions
- do not train evaluate or promote in audit milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim complete recurrent self-identification from zero-current ablation alone
- do not promote from ablation diagnostics alone
- do not run PPO or behavior cloning
- do not change actor inputs
- do not tune M581 thresholds after seeing M582/M583

## Failure Taxonomy

- none

## Scoreboard

- milestone: m584-bc-recurrent-ablation-audit
- type: gate
- checkpoint: docs/m584-bc-recurrent-ablation-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_recurrent_ablation_audit_admit_history_intervention_design
- reason: M584 concludes M582/M583 support current-response dependence but not accumulated hidden-state self-ID; next diagnostic must directly intervene on delayed or wrong recurrent history

## Next Blocker

m585-bc5660-history-intervention-design
