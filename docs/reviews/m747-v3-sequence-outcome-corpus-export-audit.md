# m747-v3-sequence-outcome-corpus-export-audit Research Review

## Summary

- Generated at UTC: 20260524T230308Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_v4_extreme_fault_coverage_design
- Decision reason: M747 preserves M746 as a clean v3 positive corpus but blocks objective PPO and true per-wheel claims then promotes to v4 extreme-fault coverage design

## Hypothesis

M746's positive v3 corpus is clean enough to preserve, but its hard-negative sparsity and proxy-fault claim boundary must be audited before objective or broader coverage work.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m746-v3-sequence-outcome-corpus-export-implementation.md, runs/m746_v3_sequence_outcome_corpus_export/summary.json, runs/m746_v3_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m746_v3_sequence_outcome_corpus_export/contrast_rows.csv, runs/m746_v3_sequence_outcome_corpus_export/hard_negative_rows.csv, runs/m746_v3_sequence_outcome_corpus_export/source_balance.csv, runs/m746_v3_sequence_outcome_corpus_export/variant_horizon_balance.csv, runs/m746_v3_sequence_outcome_corpus_export/fault_family_balance.csv
- parent_config: experiments/manifests/m746-v3-sequence-outcome-corpus-export-implementation.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_objective: audit v3 sequence-outcome corpus export and hard-negative sparsity before objective or new coverage branch
- derived_from: m746-v3-sequence-outcome-corpus-export-implementation
- blocked_by: m746-v3-sequence-outcome-corpus-export-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M747 records positive corpus pass/fail evidence
- M747 records v3 metadata and claim-boundary evidence
- M747 records hard-negative sparsity evidence
- M747 records supported and falsified claims
- M747 records public gate overfit risk
- M747 makes an explicit next branch decision
- actor update PPO and promotion remain blocked unless later designed

## Failure Criteria

- audit treats sparse hard negatives as a complete contrast set
- audit ignores sentinel normal-match or metadata checks
- audit overclaims true per-wheel physics from proxy faults
- audit admits PPO or promotion directly
- audit changes actor input contract

## Evidence Gates

- M746 positive corpus gates are audited
- M746 v3 metadata and claim-boundary preservation are audited
- M746 hard-negative sparsity is audited separately
- next branch decision compares objective design hard-negative repair v4 coverage and four-wheel fidelity
- actor training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat sparse hard negatives as a complete contrast corpus
- do not treat current-model proxy faults as true per-wheel physics
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m747-v3-sequence-outcome-corpus-export-audit
- type: gate
- checkpoint: docs/m747-v3-sequence-outcome-corpus-export-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_v4_extreme_fault_coverage_design
- reason: M747 preserves M746 as a clean v3 positive corpus but blocks objective PPO and true per-wheel claims then promotes to v4 extreme-fault coverage design

## Next Blocker

m748-v4-extreme-fault-coverage-design
