# m738-sequence-outcome-corpus-export-audit Research Review

## Summary

- Generated at UTC: 20260524T221437Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_extreme_fault_distribution_v3
- Decision reason: M738 preserves M737 clean positive corpus but treats hard-negative sparsity and user coverage hypothesis as reason to refresh extreme-fault distribution before objective work

## Hypothesis

M737's positive corpus is clean enough to preserve, but its hard-negative sparsity must be audited before objective or broader coverage work.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m737-sequence-outcome-corpus-export-implementation.md, runs/m737_sequence_outcome_corpus_export/summary.json, runs/m737_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m737_sequence_outcome_corpus_export/contrast_rows.csv, runs/m737_sequence_outcome_corpus_export/hard_negative_rows.csv, runs/m737_sequence_outcome_corpus_export/excluded_sentinel_rows.csv
- parent_config: experiments/manifests/m737-sequence-outcome-corpus-export-implementation.json
- parent_objective: audit sequence-outcome corpus export and hard-negative sparsity before objective or coverage branch
- derived_from: m737-sequence-outcome-corpus-export-implementation
- blocked_by: m737-sequence-outcome-corpus-export-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M738 records positive corpus pass/fail evidence
- M738 records hard-negative sparsity evidence
- M738 records supported and falsified claims
- M738 records public gate overfit risk
- M738 makes an explicit next branch decision
- actor update PPO and promotion remain blocked unless later designed

## Failure Criteria

- audit treats sparse hard negatives as a complete contrast set
- audit ignores sentinel or normal-match checks
- audit admits PPO or promotion directly
- audit changes actor input contract

## Evidence Gates

- M737 positive corpus gates are audited
- M737 hard-negative sparsity is audited separately
- sentinel filtering and normal matching are inspected
- next branch decision compares objective design hard-negative repair and extreme-fault distribution refresh
- actor training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat sparse hard negatives as a complete contrast corpus
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not ignore the extreme-fault coverage hypothesis
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m738-sequence-outcome-corpus-export-audit
- type: gate
- checkpoint: docs/m738-sequence-outcome-corpus-export-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_extreme_fault_distribution_v3
- reason: M738 preserves M737 clean positive corpus but treats hard-negative sparsity and user coverage hypothesis as reason to refresh extreme-fault distribution before objective work

## Next Blocker

m739-extreme-fault-distribution-v3-design
