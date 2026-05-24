# m600-bc-capability-belief-intervention-probe-design Research Review

## Summary

- Generated at UTC: 20260524T075716Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_capability_belief_intervention_probe_design_admit_m601
- Decision reason: M600 registers capability-belief intervention metrics variants thresholds and artifacts to distinguish belief movement from action movement before actor fine-tuning

## Hypothesis

The M598 capability head may reveal belief-level sensitivity to wrong or delayed recurrent histories even though M591 showed action-level insensitivity; this must be tested before actor fine-tuning.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design capability-belief intervention probe after M599 audit
- derived_from: m599-bc-capability-head-smoke-audit
- blocked_by: m599-bc-capability-head-smoke-audit
- supersedes: None
- invalidates: m600-bc-capability-guided-hidden-finetune-design

## Success Criteria

- design specifies normal reset delayed wrong shuffled scaled and random hidden variants
- design specifies capability prediction distance metrics and thresholds
- design specifies artifacts and interpretation rules
- design blocks actor fine-tuning until belief intervention evidence is known
- research validation passes

## Failure Criteria

- design jumps directly to actor fine-tuning
- design claims driver improvement from head-only prediction
- design uses capability labels as actor inputs
- design promotes a checkpoint

## Evidence Gates

- design capability intervention probe before actor fine-tuning
- reuse M591 hidden variants and M598 capability head
- pre-register belief-distance thresholds and interpretations
- keep PPO promotion and actor updates blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor or recurrent modules
- do not run PPO
- do not promote checkpoint
- do not claim driver improvement from capability prediction movement
- do not treat random-hidden sensitivity as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m600-bc-capability-belief-intervention-probe-design
- type: infrastructure
- checkpoint: docs/m600-bc-capability-belief-intervention-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_belief_intervention_probe_design_admit_m601
- reason: M600 registers capability-belief intervention metrics variants thresholds and artifacts to distinguish belief movement from action movement before actor fine-tuning

## Next Blocker

m601-bc-capability-belief-intervention-probe
