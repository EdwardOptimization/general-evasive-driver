# m592-bc-hidden-use-repair-objective-design Research Review

## Summary

- Generated at UTC: 20260524T072820Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_hidden_use_repair_objective_design_admit_capability_objective_implementation
- Decision reason: M592 selects a capability-supervised hidden repair objective with future-response regression matched-current ranking and action anchoring while blocking PPO promotion and ungrounded action separation

## Hypothesis

Because M591 shows a structural hidden path but action-equivalent real rollout hidden states, the next repair should train hidden state to encode future response or capability on matched-current histories before attempting PPO or action-level repair.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m591_bc_hidden_action_sensitivity_probe_fresh/variant_summary.csv, runs/m591_bc_hidden_action_sensitivity_probe_ood/variant_summary.csv, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design a hidden-use repair objective after M591 finds action-equivalent real hidden states
- derived_from: m591-bc-hidden-action-sensitivity-probe
- blocked_by: m591-bc-hidden-action-sensitivity-probe
- supersedes: None
- invalidates: None

## Success Criteria

- design selects the first hidden-use repair objective or corpus
- design specifies training-only targets and confirms they do not enter deployable actor inputs
- design specifies exact validation gates for hidden prediction and action sensitivity
- design blocks PPO and promotion until hidden-use evidence improves
- research validation passes

## Failure Criteria

- design adds oracle or wheel/slip inputs to the actor
- design proposes action separation without capability or outcome grounding
- design jumps directly to PPO continuation
- design promotes a checkpoint

## Evidence Gates

- design hidden-use objective or corpus before implementation
- preserve P0 human-view no-wheel no-oracle actor inputs
- avoid action-separation losses that are not tied to capability or outcome evidence
- pre-register repair validation before training

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or run PPO
- do not promote checkpoint
- do not add hidden vehicle parameters wheel slip tire force or oracle labels to actor inputs
- do not push actions apart solely for the sake of hidden sensitivity
- do not treat random-hidden sensitivity as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m592-bc-hidden-use-repair-objective-design
- type: infrastructure
- checkpoint: docs/m592-bc-hidden-use-repair-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_hidden_use_repair_objective_design_admit_capability_objective_implementation
- reason: M592 selects a capability-supervised hidden repair objective with future-response regression matched-current ranking and action anchoring while blocking PPO promotion and ungrounded action separation

## Next Blocker

m593-bc-capability-repair-objective-implementation
