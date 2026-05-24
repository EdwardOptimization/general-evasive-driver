# m757-v4-sequence-objective-design Research Review

## Summary

- Generated at UTC: 20260524T234943Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_sequence_objective_design_admit_m758
- Decision reason: M757 designs no-training exact/offline v4 sequence objective sanity over M755 positives matched normals and optional sparse hard negatives before any actor update

## Hypothesis

A constrained v4 sequence objective can be designed from M755 positives and matched normals while treating hard negatives as optional sparse contrast.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m756-v4-sequence-outcome-corpus-export-audit.md, docs/m755-v4-sequence-outcome-corpus-export-implementation.md, runs/m755_v4_sequence_outcome_corpus_export/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv, runs/m755_v4_sequence_outcome_corpus_export/hard_negative_rows.csv
- parent_config: experiments/manifests/m756-v4-sequence-outcome-corpus-export-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design constrained v4 sequence objective from clean positives with sparse hard negatives
- derived_from: m756-v4-sequence-outcome-corpus-export-audit
- blocked_by: m756-v4-sequence-outcome-corpus-export-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M757 specifies objective terms and exact metrics
- M757 specifies normal retention first-step safety and source-balance gates
- M757 specifies how sparse hard negatives are used without biasing the objective
- M757 keeps actor inputs clean and claim-boundary metadata as training-time logging only
- M757 admits only an offline/exact objective sanity implementation
- M757 blocks PPO and promotion

## Failure Criteria

- design requires hard negatives for every positive
- design drops normal-history matched rows
- design leaks hidden fault labels into actor observations
- design admits PPO or checkpoint promotion directly
- design ignores current-model/proxy claim boundary

## Evidence Gates

- M757 designs objective terms without training
- M757 treats hard negatives as sparse optional contrast
- M757 preserves normal-history behavior and first-step safety gates
- M757 preserves v4 claim-boundary metadata
- PPO checkpoint promotion and true four-wheel claims remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not assume every positive has a hard negative
- do not drop matched normal rows
- do not turn current-model/proxy labels into actor inputs
- do not start actor training
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m757-v4-sequence-objective-design
- type: infrastructure
- checkpoint: docs/m757-v4-sequence-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_objective_design_admit_m758
- reason: M757 designs no-training exact/offline v4 sequence objective sanity over M755 positives matched normals and optional sparse hard negatives before any actor update

## Next Blocker

m758-v4-sequence-objective-sanity-implementation
