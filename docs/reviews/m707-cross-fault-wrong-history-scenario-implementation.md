# m707-cross-fault-wrong-history-scenario-implementation Research Review

## Summary

- Generated at UTC: 20260524T185103Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: cross_fault_reset_only_not_source_positive
- Decision reason: M707 implements cross-fault pairing and generates 9728 scenarios 33026 snapshots and 2048 matched pairs with 15 reset-only rows but 0 wrong-history-critical rows so source export PPO and promotion remain blocked

## Hypothesis

Cross-fault wrong-history pairing will produce wrong-history-critical self-ID rows that nominal-vs-fault pairing missed.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m706-cross-fault-wrong-history-scenario-design.md, docs/m705-extreme-dynamics-scenario-corpus-audit.md, runs/m704_extreme_dynamics_scenario_corpus/summary.json
- parent_config: experiments/manifests/m706-cross-fault-wrong-history-scenario-design.json, configs/extreme_hidden_condition_scenarios.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: implement cross-fault wrong-history scenario pairing
- derived_from: m706-cross-fault-wrong-history-scenario-design
- blocked_by: m706-cross-fault-wrong-history-scenario-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- matched_cross_fault_pairs.csv is written
- fault_family_pair_summary.csv is written
- accepted_rows.csv is written
- reset_only_rows.csv is written
- rejected_rows.csv is written
- wrong-history and reset-history counts are separated
- actor checksum unchanged
- no objective actor update PPO or promotion

## Failure Criteria

- implementation mutates or trains actor
- implementation adds hidden fault labels to actor input
- implementation counts reset-only rows as source-positive
- implementation omits model-fidelity limits
- implementation admits objective design without source-positive audit

## Evidence Gates

- implementation writes cross-fault pair artifacts
- implementation reports wrong-history and reset-history rows separately
- implementation does not count reset-only rows as source-positive
- implementation preserves hidden fault labels as logging only
- actor checksum unchanged
- no objective actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add fault labels to actor observations
- do not count reset-only rows as source-positive
- do not relax wrong-history thresholds after seeing results
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m707-cross-fault-wrong-history-scenario-implementation
- type: infrastructure
- checkpoint: runs/m707_cross_fault_wrong_history_scenario/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_reset_only_not_source_positive
- reason: M707 implements cross-fault pairing and generates 9728 scenarios 33026 snapshots and 2048 matched pairs with 15 reset-only rows but 0 wrong-history-critical rows so source export PPO and promotion remain blocked

## Next Blocker

m708-cross-fault-wrong-history-scenario-audit
