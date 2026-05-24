# m745-v3-sequence-outcome-corpus-export-design Research Review

## Summary

- Generated at UTC: 20260524T225349Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v3_sequence_outcome_corpus_export_design_admit_m746
- Decision reason: M745 designs a v3-aware deterministic corpus export preserving M743 non-sentinel outcome rows source pair reset margin history and fault fidelity metadata while keeping training PPO and promotion blocked

## Hypothesis

M743's non-sentinel v3 sequence-outcome rows can be exported as a compact diverse corpus while preserving v3 source metadata.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m744-v3-reset-source-sequence-intervention-audit.md, docs/m743-v3-reset-source-sequence-intervention-implementation.md, runs/m743_v3_reset_source_sequence_intervention/summary.json, runs/m743_v3_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m743_v3_reset_source_sequence_intervention/sequence_critical_rows.csv, runs/m743_v3_reset_source_sequence_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m744-v3-reset-source-sequence-intervention-audit.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_objective: design sentinel-filtered v3 sequence-outcome corpus export after M743 positive diagnostic
- derived_from: m744-v3-reset-source-sequence-intervention-audit
- blocked_by: m744-v3-reset-source-sequence-intervention-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M745 defines positive and contrast row selection
- M745 defines v3 metadata preservation requirements
- M745 defines diversity and sentinel gates
- M745 defines export artifacts and command
- M745 blocks objective training PPO and promotion
- M745 admits only a no-training M746 implementation

## Failure Criteria

- design exports sentinel rows as positives
- design treats action-only rows as outcome positives
- design drops v3 source metadata
- design admits PPO or checkpoint promotion

## Evidence Gates

- M745 filters sentinel rows from M743 outcome positives
- M745 preserves v3-specific source and claim-boundary metadata
- M745 defines positive normal hard-negative and sentinel row roles
- M745 defines corpus diversity gates
- objective training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as outcome positives
- do not drop v3 source metadata
- do not train an actor
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m745-v3-sequence-outcome-corpus-export-design
- type: infrastructure
- checkpoint: docs/m745-v3-sequence-outcome-corpus-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v3_sequence_outcome_corpus_export_design_admit_m746
- reason: M745 designs a v3-aware deterministic corpus export preserving M743 non-sentinel outcome rows source pair reset margin history and fault fidelity metadata while keeping training PPO and promotion blocked

## Next Blocker

m746-v3-sequence-outcome-corpus-export-implementation
