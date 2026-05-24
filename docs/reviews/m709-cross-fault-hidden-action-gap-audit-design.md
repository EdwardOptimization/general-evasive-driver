# m709-cross-fault-hidden-action-gap-audit-design Research Review

## Summary

- Generated at UTC: 20260524T185746Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: hidden_action_gap_audit_design_admit_m710
- Decision reason: M709 designs a no-training cross-fault hidden/action localization audit measuring raw hidden next-hidden fused feature action and margin gaps while blocking source export PPO and promotion

## Hypothesis

A no-training hidden/action separability audit can localize why M707 cross-fault wrong histories produce reset-only but not wrong-history-critical evidence.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m708-cross-fault-wrong-history-scenario-audit.md, runs/m707_cross_fault_wrong_history_scenario/summary.json, runs/m707_cross_fault_wrong_history_scenario/matched_cross_fault_pairs.csv, runs/m707_cross_fault_wrong_history_scenario/reset_only_rows.csv
- parent_config: experiments/manifests/m708-cross-fault-wrong-history-scenario-audit.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: design no-training hidden-action separability audit for cross-fault wrong histories
- derived_from: m708-cross-fault-wrong-history-scenario-audit
- blocked_by: m708-cross-fault-wrong-history-scenario-audit
- supersedes: None
- invalidates: None

## Success Criteria

- raw hidden, next-hidden, fusion feature, action, and margin gap metrics are specified
- front/steering reset-only sentinels are identified as focused cases
- cross-fault broad rows remain included as distribution context
- actor behavior and input contract are unchanged
- no objective update actor update PPO or promotion is admitted

## Failure Criteria

- design treats reset-only rows as source-positive
- design relies on hidden fault labels as actor inputs
- design omits fusion/action localization
- design admits training before localization
- design omits model-fidelity limits

## Evidence Gates

- audit design separates raw hidden next-hidden fusion feature action and outcome gaps
- audit design focuses on front/steering reset-only sentinels without using reset-only rows as source-positive
- audit design keeps hidden fault labels as logging only
- audit design does not train or mutate actor
- audit design blocks PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add fault labels to actor observations
- do not treat raw-hidden separability alone as closed-loop proof
- do not count reset-only rows as source-positive

## Failure Taxonomy

- none

## Scoreboard

- milestone: m709-cross-fault-hidden-action-gap-audit-design
- type: infrastructure
- checkpoint: docs/m709-cross-fault-hidden-action-gap-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hidden_action_gap_audit_design_admit_m710
- reason: M709 designs a no-training cross-fault hidden/action localization audit measuring raw hidden next-hidden fused feature action and margin gaps while blocking source export PPO and promotion

## Next Blocker

m710-cross-fault-hidden-action-gap-audit-implementation
