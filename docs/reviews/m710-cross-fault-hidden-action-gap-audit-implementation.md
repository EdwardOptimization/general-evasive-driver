# m710-cross-fault-hidden-action-gap-audit-implementation Research Review

## Summary

- Generated at UTC: 20260524T190559Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: action_washout_not_source_positive
- Decision reason: M710 finds wrong-history signal at raw hidden and fused feature levels but 0 wrong action-positive and 0 wrong outcome-positive rows so source export PPO and promotion remain blocked

## Hypothesis

Cross-fault wrong histories either collapse before the actor action boundary or expose a specific hidden/action washout point that explains M707's reset-only result.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m709-cross-fault-hidden-action-gap-audit-design.md, docs/m708-cross-fault-wrong-history-scenario-audit.md, runs/m707_cross_fault_wrong_history_scenario/summary.json
- parent_config: experiments/manifests/m709-cross-fault-hidden-action-gap-audit-design.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: implement no-training hidden-action separability audit for cross-fault wrong histories
- derived_from: m709-cross-fault-hidden-action-gap-audit-design
- blocked_by: m709-cross-fault-hidden-action-gap-audit-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- row_hidden_action_gaps.csv is written
- variant_summary.csv is written
- fault family pair variant summaries are written
- sentinel summaries are written
- result class is assigned
- actor checksum unchanged
- no objective actor update PPO or promotion

## Failure Criteria

- implementation mutates or trains actor
- implementation adds hidden fault labels to actor input
- implementation counts reset-only rows as source-positive
- implementation omits raw hidden or fused feature gap metrics
- implementation admits objective design without source-positive audit

## Evidence Gates

- summary.json is written
- row_hidden_action_gaps.csv is written
- variant_summary.csv is written
- fault_family_pair_variant_summary.csv is written
- sentinel_summary.csv is written
- raw hidden next-hidden fused feature action and margin gaps are separated
- actor checksum unchanged
- no objective actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor observations
- do not treat reset-only rows as source-positive
- do not relax thresholds after seeing results
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m710-cross-fault-hidden-action-gap-audit-implementation
- type: infrastructure
- checkpoint: runs/m710_cross_fault_hidden_action_gap_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_washout_not_source_positive
- reason: M710 finds wrong-history signal at raw hidden and fused feature levels but 0 wrong action-positive and 0 wrong outcome-positive rows so source export PPO and promotion remain blocked

## Next Blocker

m711-cross-fault-hidden-action-gap-audit
