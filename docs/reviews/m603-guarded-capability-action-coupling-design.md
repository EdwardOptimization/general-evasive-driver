# m603-guarded-capability-action-coupling-design Research Review

## Summary

- Generated at UTC: 20260524T082505Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: guarded_capability_action_coupling_design_admit_m604_evaluator
- Decision reason: M603 designs an exact no-update coupling-gap evaluator and grounded action-coupling requirements before any actor update or PPO

## Hypothesis

Because M601 shows belief-level real-history movement while M591 shows weak action-level movement, the next repair should be a guarded capability-to-action coupling design rather than PPO or ungrounded action contrast.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m601_bc_capability_belief_intervention_fresh/summary.json, runs/m601_bc_capability_belief_intervention_ood/summary.json, runs/m591_bc_hidden_action_sensitivity_probe_fresh/summary.json, runs/m591_bc_hidden_action_sensitivity_probe_ood/summary.json
- parent_config: docs/m602-bc-capability-belief-intervention-audit.md
- parent_objective: design a guarded no-oracle objective that couples decoded capability belief to action without ungrounded action separation
- derived_from: m602-bc-capability-belief-intervention-audit
- blocked_by: m602-bc-capability-belief-intervention-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design states exact objective terms and forbidden shortcuts
- design separates no-update evaluator from future optimizer step
- design specifies which rows can request action movement and why
- design keeps P0 actor inputs unchanged and PPO blocked
- research validation passes

## Failure Criteria

- design starts training
- design adds privileged actor inputs
- design treats capability movement as driver improvement
- design omits action-retention anchors
- design permits ungrounded action separation

## Evidence Gates

- define allowed training-only capability signals
- define normal action-retention anchors
- define grounded rows where action movement is allowed
- define exact no-update sanity evaluator before any optimizer step
- keep actor input contract unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not run PPO
- do not promote checkpoint
- do not add capability labels to actor inputs
- do not force action separation without a grounded recovery or boundary target

## Failure Taxonomy

- none

## Scoreboard

- milestone: m603-guarded-capability-action-coupling-design
- type: infrastructure
- checkpoint: docs/m603-guarded-capability-action-coupling-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_capability_action_coupling_design_admit_m604_evaluator
- reason: M603 designs an exact no-update coupling-gap evaluator and grounded action-coupling requirements before any actor update or PPO

## Next Blocker

m604-guarded-capability-action-coupling-objective-implementation
