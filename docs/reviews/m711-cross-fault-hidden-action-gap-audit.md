# m711-cross-fault-hidden-action-gap-audit Research Review

## Summary

- Generated at UTC: 20260524T190902Z
- Type: gate
- Gate tier: process
- Promotion decision: action_washout_audit_pivot_actor_head_coupling
- Decision reason: M711 audits M710 as feature-distance metric artifact with wrong-history signal surviving to fused features but not deployed action or margin so the branch pivots to actor-head history-signal coupling

## Hypothesis

M710 action_washout should block source export and redirect the next step toward actor-head or objective-level handling of existing fused history signal.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m710_cross_fault_hidden_action_gap_audit/summary.json, runs/m710_cross_fault_hidden_action_gap_audit/row_hidden_action_gaps.csv, runs/m710_cross_fault_hidden_action_gap_audit/variant_summary.csv, docs/m710-cross-fault-hidden-action-gap-audit-implementation.md
- parent_config: experiments/manifests/m710-cross-fault-hidden-action-gap-audit-implementation.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: audit action_washout hidden-action gap result before any actor update or PPO
- derived_from: m710-cross-fault-hidden-action-gap-audit-implementation
- blocked_by: m710-cross-fault-hidden-action-gap-audit-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M710 summary metrics are recorded
- action_washout is classified
- supported and falsified claims are recorded
- failure taxonomy is assigned
- public gate overfit risk is recorded
- next branch decision is explicit
- source export actor update PPO and promotion remain blocked unless a new evidence path is justified

## Failure Criteria

- audit treats raw hidden or fused feature gap as source-positive proof
- audit admits PPO without proof-retaining objective design
- audit ignores reset-only overclaim risk
- audit omits synthesis questions
- audit changes actor input contract

## Evidence Gates

- M710 implementation cleanliness is checked
- action_washout is separated from source-positive history incompatibility
- raw hidden fused feature and action gaps are summarized
- reset-hidden disruption is not treated as wrong-history proof
- source export actor update PPO and promotion remain blocked unless the audit explicitly justifies otherwise
- extreme_hidden_condition_scenario_generation branch receives a synthesis decision if needed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat raw or fused feature gap alone as closed-loop self-ID proof
- do not train actor from M710 rows without an audit
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor inputs
- do not ignore reset-only overclaim risk

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m711-cross-fault-hidden-action-gap-audit
- type: gate
- checkpoint: docs/m711-cross-fault-hidden-action-gap-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_washout_audit_pivot_actor_head_coupling
- reason: M711 audits M710 as feature-distance metric artifact with wrong-history signal surviving to fused features but not deployed action or margin so the branch pivots to actor-head history-signal coupling

## Next Blocker

m712-actor-head-history-signal-coupling-design
