# m708-cross-fault-wrong-history-scenario-audit Research Review

## Summary

- Generated at UTC: 20260524T185421Z
- Type: gate
- Gate tier: process
- Promotion decision: cross_fault_reset_only_audit_continue_hidden_action_localization
- Decision reason: M708 classifies M707 as metric_artifact plus scenario_sampling_failure because wrong-history action gaps never reach threshold while reset-hidden action gaps do; source export PPO and promotion remain blocked

## Hypothesis

M707 cross_fault_reset_only should block source export and synthesize whether the next step is stronger history incompatibility, active probing, or higher-fidelity fault modeling.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m707_cross_fault_wrong_history_scenario/summary.json, runs/m707_cross_fault_wrong_history_scenario/matched_cross_fault_pairs.csv, runs/m707_cross_fault_wrong_history_scenario/fault_family_pair_summary.csv, runs/m707_cross_fault_wrong_history_scenario/reset_only_rows.csv, docs/m707-cross-fault-wrong-history-scenario-implementation.md
- parent_config: experiments/manifests/m707-cross-fault-wrong-history-scenario-implementation.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: audit cross_fault_reset_only result before any source export or training
- derived_from: m707-cross-fault-wrong-history-scenario-implementation
- blocked_by: m707-cross-fault-wrong-history-scenario-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M707 summary metrics are recorded
- fault-family pair reset-only concentration is recorded
- wrong-history zero result is classified
- scenario coverage hypothesis is updated
- supported and falsified claims are recorded
- failure taxonomy is assigned
- next branch decision is explicit
- source export actor update PPO and promotion remain blocked unless a new evidence path is justified

## Failure Criteria

- audit treats reset-only rows as wrong-history self-ID evidence
- audit admits source export from empty accepted_rows.csv
- audit omits model-fidelity limits
- audit omits synthesis questions
- audit changes actor input contract

## Evidence Gates

- M707 implementation cleanliness is checked
- wrong-history zero result is separated from reset-only evidence
- fault-family pair summaries are audited
- scenario coverage hypothesis is updated
- model-fidelity limits are preserved
- source export actor update PPO and promotion remain blocked unless the audit explicitly justifies otherwise
- extreme_hidden_condition_scenario_generation branch receives a synthesis decision

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as source-positive
- do not export accepted_rows.csv because it is empty
- do not lower wrong-history thresholds after seeing M707
- do not run actor update
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels to actor inputs

## Failure Taxonomy

- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m708-cross-fault-wrong-history-scenario-audit
- type: gate
- checkpoint: docs/m708-cross-fault-wrong-history-scenario-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_reset_only_audit_continue_hidden_action_localization
- reason: M708 classifies M707 as metric_artifact plus scenario_sampling_failure because wrong-history action gaps never reach threshold while reset-hidden action gaps do; source export PPO and promotion remain blocked

## Next Blocker

m709-cross-fault-hidden-action-gap-audit-design
