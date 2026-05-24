# m576-moderate-ood-route-eval-audit Research Review

## Summary

- Generated at UTC: 20260524T062146Z
- Type: gate
- Gate tier: process
- Promotion decision: moderate_ood_audit_admit_bc_family_repeat_design
- Decision reason: M576 audits M570/M572/M575 positive BC5660 evidence rejects immediate promotion/PPO and admits BC seed-family repeats

## Hypothesis

Because BC5660 now matches L2 on public fresh-route and moderate-OOD diagnostics, the next step should be chosen by an evidence audit rather than immediately promoting or running PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json, runs/m572_fresh_route_generalization_eval/summary.json, runs/m575_moderate_ood_route_generalization_eval/summary.json
- parent_config: configs/eval_m574_moderate_ood_l0.json, configs/eval_m574_moderate_ood_l2.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: audit scaled BC public fresh-route and moderate-OOD evidence before escalation
- derived_from: m575-moderate-ood-route-generalization-eval
- blocked_by: m575-moderate-ood-route-generalization-eval
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes M570 M572 and M575 metrics and limitations
- audit identifies the next blocker and escalation path
- audit explicitly rejects immediate promotion unless evidence gaps are closed
- research validation passes

## Failure Criteria

- audit ignores M575 limitations
- audit treats public or single-block OOD diagnostics as private promotion evidence
- audit allows PPO or promotion without repeat/generalization/ablation evidence

## Evidence Gates

- audit M570 M572 and M575 evidence side by side
- identify remaining evidence gaps before promotion or PPO
- decide whether next step should be BC seed-family repeat OOD repeat or recurrent ablation
- do not train or promote in audit milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from M575 single OOD gate
- do not tune from M575 before documenting the audit
- do not run PPO or behavior cloning
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m576-moderate-ood-route-eval-audit
- type: gate
- checkpoint: docs/m576-moderate-ood-route-eval-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: moderate_ood_audit_admit_bc_family_repeat_design
- reason: M576 audits M570/M572/M575 positive BC5660 evidence rejects immediate promotion/PPO and admits BC seed-family repeats

## Next Blocker

m577-bc-family-generalization-repeat-design
