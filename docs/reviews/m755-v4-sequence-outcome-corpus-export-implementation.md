# m755-v4-sequence-outcome-corpus-export-implementation Research Review

## Summary

- Generated at UTC: 20260524T234438Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_sequence_outcome_corpus_hard_negative_sparse
- Decision reason: M755 exports 1213 clean v4 sequence-outcome positives with matched normals preserved v4 metadata and 1009 sparse hard negatives so objective work remains blocked pending audit

## Hypothesis

M752's non-sentinel v4 sequence-outcome rows can be exported as a compact corpus with matched normal rows, separated hard negatives, and preserved v4 metadata.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m754-v4-sequence-outcome-corpus-export-design.md, docs/m753-v4-reset-source-sequence-intervention-audit.md, runs/m752_v4_reset_source_sequence_intervention/summary.json, runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m752_v4_reset_source_sequence_intervention/sequence_critical_rows.csv, runs/m752_v4_reset_source_sequence_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m754-v4-sequence-outcome-corpus-export-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: implement deterministic sentinel-filtered v4 sequence-outcome corpus export
- derived_from: m754-v4-sequence-outcome-corpus-export-design
- blocked_by: m754-v4-sequence-outcome-corpus-export-design
- supersedes: None
- invalidates: None

## Success Criteria

- M755 implements deterministic v4-aware exporter and focused tests
- M755 writes summary positive contrast hard-negative sentinel rejected and balance artifacts
- positive_rows >= 1000
- positive_sentinel_rows == 0
- missing_normal_matches == 0
- unique_positive_seeds >= 24
- unique_positive_fault_family_pairs >= 16
- max_positive_seed_dominance <= 0.20
- v4 source claim-boundary and fault fidelity metadata are preserved
- hard_negative_rows are marked separately from proof positives
- no actor training PPO checkpoint loading or promotion occurs

## Failure Criteria

- sentinel rows enter positive corpus
- action-only rows enter positive corpus
- normal matches are missing
- v4 source metadata is dropped
- fault fidelity or claim-boundary metadata is missing
- source balance falls below registered gates
- implementation starts optimizer training PPO checkpoint loading or promotion

## Evidence Gates

- M755 exports only non-sentinel sequence-outcome positives
- M755 matches every positive with a normal row
- M755 marks hard negatives separately from proof positives
- M755 preserves v4 source pair reset margin history and claim-boundary metadata
- actor training PPO checkpoint loading and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as positives
- do not drop v4 source metadata
- do not omit current-model versus proxy claim-boundary fields
- do not instantiate actor training or PPO
- do not load or promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m755-v4-sequence-outcome-corpus-export-implementation
- type: infrastructure
- checkpoint: runs/m755_v4_sequence_outcome_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_outcome_corpus_hard_negative_sparse
- reason: M755 exports 1213 clean v4 sequence-outcome positives with matched normals preserved v4 metadata and 1009 sparse hard negatives so objective work remains blocked pending audit

## Next Blocker

m756-v4-sequence-outcome-corpus-export-audit
