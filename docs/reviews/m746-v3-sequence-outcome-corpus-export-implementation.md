# m746-v3-sequence-outcome-corpus-export-implementation Research Review

## Summary

- Generated at UTC: 20260524T225958Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v3_sequence_outcome_corpus_hard_negative_sparse
- Decision reason: M746 exports 995 clean v3 sequence-outcome positives with 995 matched normals 0 sentinel positives 0 missing metadata and 992 capped hard negatives so positive corpus passes but hard-negative contrast remains slightly sparse

## Hypothesis

M743's non-sentinel v3 sequence-outcome rows can be exported as a compact corpus with matched normal rows, separated hard negatives, and preserved v3 metadata.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m745-v3-sequence-outcome-corpus-export-design.md, docs/m744-v3-reset-source-sequence-intervention-audit.md, runs/m743_v3_reset_source_sequence_intervention/summary.json, runs/m743_v3_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m743_v3_reset_source_sequence_intervention/sequence_critical_rows.csv, runs/m743_v3_reset_source_sequence_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m745-v3-sequence-outcome-corpus-export-design.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_objective: implement deterministic sentinel-filtered v3 sequence-outcome corpus export
- derived_from: m745-v3-sequence-outcome-corpus-export-design
- blocked_by: m745-v3-sequence-outcome-corpus-export-design
- supersedes: None
- invalidates: None

## Success Criteria

- M746 implements deterministic v3-aware exporter and focused tests
- M746 writes summary positive contrast hard-negative sentinel rejected and balance artifacts
- positive_rows >= 500
- positive_sentinel_rows == 0
- missing_normal_matches == 0
- unique_positive_seeds >= 16
- unique_positive_fault_family_pairs >= 16
- max_positive_seed_dominance <= 0.20
- v3 source and fault fidelity metadata are preserved
- hard_negative_rows are marked separately from proof positives
- no actor training PPO checkpoint loading or promotion occurs

## Failure Criteria

- sentinel rows enter positive corpus
- action-only rows enter positive corpus
- normal matches are missing
- v3 source metadata is dropped
- fault fidelity metadata is missing
- source balance falls below registered gates
- implementation starts optimizer training PPO checkpoint loading or promotion

## Evidence Gates

- M746 exports only non-sentinel sequence-outcome positives
- M746 matches every positive with a normal row
- M746 marks hard negatives separately from proof positives
- M746 preserves v3 source pair reset margin history and fidelity metadata
- actor training PPO checkpoint loading and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as positives
- do not drop v3 source metadata
- do not omit current-model versus proxy claim-boundary fields
- do not instantiate actor training or PPO
- do not load or promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m746-v3-sequence-outcome-corpus-export-implementation
- type: infrastructure
- checkpoint: runs/m746_v3_sequence_outcome_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v3_sequence_outcome_corpus_hard_negative_sparse
- reason: M746 exports 995 clean v3 sequence-outcome positives with 995 matched normals 0 sentinel positives 0 missing metadata and 992 capped hard negatives so positive corpus passes but hard-negative contrast remains slightly sparse

## Next Blocker

m747-v3-sequence-outcome-corpus-export-audit
