# m754-v4-sequence-outcome-corpus-export-design Research Review

## Summary

- Generated at UTC: 20260524T234052Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_sequence_outcome_corpus_export_design_admit_m755
- Decision reason: M754 designs v4-aware deterministic corpus export preserving M752 non-sentinel outcome rows source metadata claim-boundary fields and sparse hard-negative reporting before objective work

## Hypothesis

M752's non-sentinel v4 sequence-outcome rows can be exported as a compact diverse corpus while preserving v4 source and claim-boundary metadata.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m753-v4-reset-source-sequence-intervention-audit.md, docs/m752-v4-reset-source-sequence-intervention-implementation.md, runs/m752_v4_reset_source_sequence_intervention/summary.json, runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m752_v4_reset_source_sequence_intervention/sequence_critical_rows.csv, runs/m752_v4_reset_source_sequence_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m753-v4-reset-source-sequence-intervention-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design sentinel-filtered v4 sequence-outcome corpus export after M752 positive diagnostic
- derived_from: m753-v4-reset-source-sequence-intervention-audit
- blocked_by: m753-v4-reset-source-sequence-intervention-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M754 defines positive and contrast row selection
- M754 defines v4 metadata preservation requirements
- M754 defines diversity and sentinel gates
- M754 defines export artifacts and command
- M754 blocks objective training PPO and promotion
- M754 admits only a no-training M755 implementation

## Failure Criteria

- design exports sentinel rows as positives
- design treats action-only rows as outcome positives
- design drops v4 source or claim-boundary metadata
- design admits PPO or checkpoint promotion

## Evidence Gates

- M754 filters sentinel rows from M752 outcome positives
- M754 preserves v4-specific source and claim-boundary metadata
- M754 defines positive normal hard-negative and sentinel row roles
- M754 defines corpus diversity gates
- objective training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as outcome positives
- do not drop v4 source metadata
- do not overclaim current proxy faults as true four-wheel physics
- do not train an actor
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m754-v4-sequence-outcome-corpus-export-design
- type: infrastructure
- checkpoint: docs/m754-v4-sequence-outcome-corpus-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_outcome_corpus_export_design_admit_m755
- reason: M754 designs v4-aware deterministic corpus export preserving M752 non-sentinel outcome rows source metadata claim-boundary fields and sparse hard-negative reporting before objective work

## Next Blocker

m755-v4-sequence-outcome-corpus-export-implementation
