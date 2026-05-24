# m712-actor-head-history-signal-coupling-design Research Review

## Summary

- Generated at UTC: 20260524T191138Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: actor_head_coupling_design_admit_m713
- Decision reason: M712 designs a no-training actor-head sensitivity audit with projection tanh attenuation and feature-delta amplification line search while blocking actor update PPO and promotion

## Hypothesis

A no-training actor-head sensitivity audit can determine why M710 fused wrong-history feature differences do not produce action differences.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m711-cross-fault-hidden-action-gap-audit.md, runs/m710_cross_fault_hidden_action_gap_audit/summary.json, runs/m710_cross_fault_hidden_action_gap_audit/row_hidden_action_gaps.csv
- parent_config: experiments/manifests/m711-cross-fault-hidden-action-gap-audit.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: design no-training actor-head sensitivity audit for cross-fault fused history signal
- derived_from: m711-cross-fault-hidden-action-gap-audit
- blocked_by: m711-cross-fault-hidden-action-gap-audit
- supersedes: None
- invalidates: None

## Success Criteria

- pre-tanh actor-head projection metrics are specified
- tanh derivative attenuation metrics are specified
- wrong-vs-reset direction comparison is specified
- feature-delta amplification line search is specified
- actor behavior and input contract are unchanged
- no objective update actor update PPO or promotion is admitted

## Failure Criteria

- design changes actor inputs
- design treats amplified counterfactual actions as deployed behavior
- design omits projection or tanh attenuation
- design admits training before no-training audit
- design omits reset-hidden comparison

## Evidence Gates

- design separates feature-delta size projection tanh attenuation and action output
- design compares wrong-history directions with reset-hidden directions
- design includes feature-delta amplification line search
- design keeps actor inputs unchanged
- design blocks actor update PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor observations
- do not treat amplified feature actions as deployed behavior
- do not claim closed-loop self-ID proof from actor-head projection alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m712-actor-head-history-signal-coupling-design
- type: infrastructure
- checkpoint: docs/m712-actor-head-history-signal-coupling-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: actor_head_coupling_design_admit_m713
- reason: M712 designs a no-training actor-head sensitivity audit with projection tanh attenuation and feature-delta amplification line search while blocking actor update PPO and promotion

## Next Blocker

m713-actor-head-history-signal-coupling-implementation
