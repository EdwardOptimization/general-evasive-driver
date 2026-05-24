# m737-sequence-outcome-corpus-export-implementation Research Review

## Summary

- Generated at UTC: 20260524T221154Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: sequence_outcome_corpus_hard_negative_sparse
- Decision reason: M737 exports 70 clean sequence-outcome positives with matched normal rows but only 63 same-horizon hard negatives so objective design remains blocked pending audit

## Hypothesis

M734's non-sentinel sequence-outcome rows can be exported as a compact corpus with matched normal and hard-negative contrast rows.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m736-sequence-outcome-corpus-export-design.md, docs/m735-sequence-level-command-response-intervention-audit.md, runs/m734_sequence_command_response_intervention/summary.json, runs/m734_sequence_command_response_intervention/intervention_rollouts.csv, runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv, runs/m734_sequence_command_response_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m736-sequence-outcome-corpus-export-design.json
- parent_objective: implement deterministic sentinel-filtered sequence-outcome corpus export
- derived_from: m736-sequence-outcome-corpus-export-design
- blocked_by: m736-sequence-outcome-corpus-export-design
- supersedes: None
- invalidates: None

## Success Criteria

- M737 implements deterministic exporter and focused tests
- M737 writes summary positive contrast hard-negative sentinel rejected and balance artifacts
- positive_rows >= 50
- positive_sentinel_rows == 0
- missing_normal_matches == 0
- unique_positive_seeds >= 20
- unique_positive_fault_family_pairs >= 6
- hard_negative_rows are marked separately from proof positives
- no actor training PPO checkpoint loading or promotion occurs

## Failure Criteria

- sentinel rows enter positive corpus
- action-only rows enter positive corpus
- normal matches are missing
- source balance falls below registered gates
- implementation starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- M737 exports only non-sentinel sequence-outcome positives
- M737 matches every positive with a normal row
- M737 marks hard negatives separately from proof positives
- M737 reports source variant horizon and sentinel balance
- actor training PPO checkpoint loading and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as positives
- do not omit matched normal rows
- do not instantiate actor training or PPO
- do not load or promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m737-sequence-outcome-corpus-export-implementation
- type: infrastructure
- checkpoint: runs/m737_sequence_outcome_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_outcome_corpus_hard_negative_sparse
- reason: M737 exports 70 clean sequence-outcome positives with matched normal rows but only 63 same-horizon hard negatives so objective design remains blocked pending audit

## Next Blocker

m738-sequence-outcome-corpus-export-audit
