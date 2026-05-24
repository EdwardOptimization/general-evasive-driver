# m758-v4-sequence-objective-sanity-implementation Research Review

## Summary

- Generated at UTC: 20260524T235607Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_sequence_objective_hard_negative_sparse
- Decision reason: M758 reconstructs 1213 of 1213 M755 samples with finite exact metrics and no actor mutation but hard-negative availability remains sparse at 0.721352

## Hypothesis

The M755 v4 corpus can be reconstructed into exact objective samples with finite normal retention and intervention-gap metrics without training the actor.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m757-v4-sequence-objective-design.md, runs/m755_v4_sequence_outcome_corpus_export/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m757-v4-sequence-objective-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: implement exact/offline v4 sequence objective sanity evaluator without actor update
- derived_from: m757-v4-sequence-objective-design
- blocked_by: m757-v4-sequence-objective-design
- supersedes: None
- invalidates: None

## Success Criteria

- M758 implements objective sanity evaluator and focused tests
- M758 reconstructs M755 positive groups from seed fault step source metadata
- sample_reconstruction_success_rate >= 0.98
- metadata_missing_rows == 0
- normal_intervention_gap_mean >= 0.02
- exact losses are finite
- hard-negative sparsity is reported not hidden
- no actor training PPO or promotion occurs

## Failure Criteria

- source snapshots cannot be reconstructed
- normal rows or positive intervention rows cannot be matched
- objective drops positives without hard negatives
- v4 claim-boundary metadata is missing
- implementation starts optimizer training PPO checkpoint writing or promotion

## Evidence Gates

- M758 reconstructs objective samples from M755 corpus rows
- M758 computes exact full-corpus objective metrics without training
- M758 reports hard-negative availability separately
- M758 preserves v4 claim-boundary metadata
- PPO actor update checkpoint promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor parameters
- do not run PPO
- do not promote a checkpoint
- do not use hidden fault labels as actor inputs
- do not discard positives without hard negatives
- do not treat action-only rows as outcome positives

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m758-v4-sequence-objective-sanity-implementation
- type: infrastructure
- checkpoint: runs/m758_v4_sequence_objective_sanity/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_objective_hard_negative_sparse
- reason: M758 reconstructs 1213 of 1213 M755 samples with finite exact metrics and no actor mutation but hard-negative availability remains sparse at 0.721352

## Next Blocker

m759-v4-sequence-objective-sanity-audit
