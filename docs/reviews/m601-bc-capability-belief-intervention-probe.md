# m601-bc-capability-belief-intervention-probe Research Review

## Summary

- Generated at UTC: 20260524T081751Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_capability_belief_intervention_probe_pass_admit_audit
- Decision reason: M601 finds belief-level real-history movement: shuffled passes on fresh and OOD and wrong-matched passes on OOD while delayed remains weak; no actor training PPO promotion or driver claim

## Hypothesis

If M598 learned a meaningful hidden capability belief, wrong or delayed real histories may change capability predictions even though M591 showed action-level insensitivity.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt, runs/m598_bc_capability_repair_head_only_smoke/summary.json, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: implement and run capability-belief intervention probe after M600 design
- derived_from: m600-bc-capability-belief-intervention-probe-design
- blocked_by: m600-bc-capability-belief-intervention-probe-design
- supersedes: None
- invalidates: None

## Success Criteria

- fresh and OOD summary.json files exist
- variant summaries include all M600 variants
- capability z-distance threshold is 0.25
- milestone doc applies the M600 interpretation rules
- research validation and focused tests pass

## Failure Criteria

- probe trains any model
- probe omits wrong or delayed history variants
- probe treats random hidden movement as self-ID proof
- probe promotes a checkpoint

## Evidence Gates

- run fresh capability-belief intervention surface
- run OOD capability-belief intervention surface
- summarize normal reset delayed wrong shuffled scaled random and observation-control variants
- decide whether actor fine-tune design is admitted

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor or capability head
- do not run PPO
- do not promote checkpoint
- do not claim driver improvement from belief movement
- do not treat random-hidden sensitivity as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m601-bc-capability-belief-intervention-probe
- type: gate
- checkpoint: runs/m601_bc_capability_belief_intervention_fresh/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_belief_intervention_probe_pass_admit_audit
- reason: M601 finds belief-level real-history movement: shuffled passes on fresh and OOD and wrong-matched passes on OOD while delayed remains weak; no actor training PPO promotion or driver claim

## Next Blocker

m602-bc-capability-belief-intervention-audit
