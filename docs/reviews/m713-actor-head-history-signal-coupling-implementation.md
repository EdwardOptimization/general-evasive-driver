# m713-actor-head-history-signal-coupling-implementation Research Review

## Summary

- Generated at UTC: 20260524T192231Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: actor_head_coupling_positive_admit_audit
- Decision reason: M713 finds 164 wrong-history rows crossing action threshold by alpha 4 across 20 fault pairs while keeping actor checksum unchanged and blocking actor update PPO and promotion

## Hypothesis

The M710 action_washout can be localized to actor-head projection, tanh attenuation, or feature delta amplitude using a no-training feature-line-search audit.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m712-actor-head-history-signal-coupling-design.md, docs/m711-cross-fault-hidden-action-gap-audit.md, runs/m710_cross_fault_hidden_action_gap_audit/summary.json
- parent_config: experiments/manifests/m712-actor-head-history-signal-coupling-design.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: implement no-training actor-head history-signal coupling audit
- derived_from: m712-actor-head-history-signal-coupling-design
- blocked_by: m712-actor-head-history-signal-coupling-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- row_actor_head_coupling.csv is written
- variant and fault-pair summaries are written
- alpha line-search summaries are written
- result class is assigned
- actor checksum unchanged
- no objective actor update PPO or promotion

## Failure Criteria

- implementation mutates or trains actor
- implementation adds hidden fault labels to actor input
- implementation treats amplified counterfactual actions as deployed behavior
- implementation omits projection or tanh attenuation metrics
- implementation admits objective design without audit

## Evidence Gates

- summary.json is written
- row_actor_head_coupling.csv is written
- variant_summary.csv is written
- fault_family_pair_variant_summary.csv is written
- sentinel_summary.csv is written
- alpha_summary.csv is written
- feature projection tanh attenuation and alpha line-search metrics are separated
- actor checksum unchanged
- no objective actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor observations
- do not treat amplified feature actions as deployed behavior
- do not relax alpha thresholds after seeing results
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m713-actor-head-history-signal-coupling-implementation
- type: infrastructure
- checkpoint: runs/m713_actor_head_history_signal_coupling/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: actor_head_coupling_positive_admit_audit
- reason: M713 finds 164 wrong-history rows crossing action threshold by alpha 4 across 20 fault pairs while keeping actor checksum unchanged and blocking actor update PPO and promotion

## Next Blocker

m714-actor-head-history-signal-coupling-audit
