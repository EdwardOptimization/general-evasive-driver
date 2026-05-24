# m714-actor-head-history-signal-coupling-audit Research Review

## Summary

- Generated at UTC: 20260524T193344Z
- Type: gate
- Gate tier: process
- Promotion decision: actor_head_coupling_positive_promote_to_extreme_fault_coverage_refresh
- Decision reason: M714 classifies M713 as a positive counterfactual actor-head coupling diagnostic but blocks direct actor update PPO promotion and opens a broader extreme-fault coverage refresh

## Hypothesis

M713 actor_head_coupling_positive should admit conservative objective design in principle while blocking direct actor update PPO and promotion; it does not rule out a broader extreme-fault coverage refresh before objective design.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m713_actor_head_history_signal_coupling/summary.json, runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv, runs/m713_actor_head_history_signal_coupling/alpha_summary.csv, docs/m713-actor-head-history-signal-coupling-implementation.md
- parent_config: experiments/manifests/m713-actor-head-history-signal-coupling-implementation.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: audit actor_head_coupling_positive before any objective design or actor update
- derived_from: m713-actor-head-history-signal-coupling-implementation
- blocked_by: m713-actor-head-history-signal-coupling-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M713 summary metrics are recorded
- feature-line-search positives are classified
- supported and falsified claims are recorded
- failure taxonomy is assigned
- public gate overfit risk is recorded
- next branch decision is explicit
- actor update PPO and promotion remain blocked unless a new objective design is pre-registered after the coverage decision

## Failure Criteria

- audit treats amplified counterfactual actions as deployed behavior
- audit admits PPO without objective design and coverage decision
- audit ignores source diversity or alpha thresholds
- audit omits synthesis questions
- audit changes actor input contract

## Evidence Gates

- M713 implementation cleanliness is checked
- feature-line-search positives are separated from deployed actor behavior
- source diversity and alpha thresholds are summarized
- objective-design admission or deferral is explicit
- actor update PPO and promotion remain blocked unless the audit explicitly justifies otherwise
- actor_head_history_signal_coupling branch receives a synthesis decision

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat amplified feature actions as deployed behavior
- do not claim closed-loop self-ID proof from M713
- do not run actor update
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m714-actor-head-history-signal-coupling-audit
- type: gate
- checkpoint: docs/m714-actor-head-history-signal-coupling-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: actor_head_coupling_positive_promote_to_extreme_fault_coverage_refresh
- reason: M714 classifies M713 as a positive counterfactual actor-head coupling diagnostic but blocks direct actor update PPO promotion and opens a broader extreme-fault coverage refresh

## Next Blocker

m715-extreme-fault-coverage-refresh-design
