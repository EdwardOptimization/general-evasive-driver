# m640-source-diverse-sequence-target-corpus-design Research Review

## Summary

- Generated at UTC: 20260524T121600Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_diverse_sequence_target_corpus_design_admit_m641
- Decision reason: M640 designs capped source-balanced CSV plus NPZ sequence target corpus with heldout-source split and keeps training blocked

## Hypothesis

M639's source-diverse accepted sequence candidates can be converted into a source-balanced target corpus without letting high-count sources dominate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m639_combined_shape_source_diversity_expansion/summary.json, runs/m639_combined_shape_source_diversity_expansion/accepted_expanded_sequences.csv, runs/m639_combined_shape_source_diversity_expansion/source_recovery_summary.csv, runs/m639_combined_shape_source_diversity_expansion/source_diversity_summary.csv, docs/m639-combined-shape-source-diversity-expansion-implementation.md
- parent_config: experiments/manifests/m639-combined-shape-source-diversity-expansion-implementation.json, docs/m638-combined-shape-source-diversity-expansion-design.md
- parent_objective: design source-balanced sequence target corpus from M639 accepted candidates
- derived_from: m639-combined-shape-source-diversity-expansion-implementation
- blocked_by: m639-combined-shape-source-diversity-expansion-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies per-source and per-grid caps
- design specifies train validation and source-heldout splits
- design specifies corpus fields and weighting rules
- design keeps training PPO and promotion blocked
- research validation passes

## Failure Criteria

- design starts training
- design promotes checkpoint
- design uses raw accepted candidate count as sampling weights
- design omits heldout sources
- design violates actor input contract

## Evidence Gates

- define source-balanced sampling or caps for M639 accepted sequences
- preserve source grid target and surface diversity
- define train validation and source-heldout split rules
- define corpus weights without changing actor inputs
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not feed source labels or target labels into actor input
- do not let raw candidate count dominate corpus weights
- do not skip source-heldout design
- do not admit optimizer training directly

## Failure Taxonomy

- none

## Scoreboard

- milestone: m640-source-diverse-sequence-target-corpus-design
- type: infrastructure
- checkpoint: docs/m640-source-diverse-sequence-target-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_sequence_target_corpus_design_admit_m641
- reason: M640 designs capped source-balanced CSV plus NPZ sequence target corpus with heldout-source split and keeps training blocked

## Next Blocker

m641-source-diverse-sequence-target-corpus-implementation
