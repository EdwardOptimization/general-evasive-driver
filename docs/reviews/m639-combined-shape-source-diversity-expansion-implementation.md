# m639-combined-shape-source-diversity-expansion-implementation Research Review

## Summary

- Generated at UTC: 20260524T121309Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: combined_shape_source_diversity_expansion_pass_admit_corpus_design
- Decision reason: M639 accepts all 9 trust-primary non-collision sources across 8 physical pairs 6 left seeds 2 surfaces and 3 targets while preserving trust limits

## Hypothesis

The M636 combined projected-shape method may recover a source-diverse trust-primary non-collision subset when applied to the broader M627 near-miss source set.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m627_near_miss_trust_geometry/near_miss_sources.csv, runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv, runs/m636_combined_source7_preserving_shape/source_recovery_summary.csv, docs/m638-combined-shape-source-diversity-expansion-design.md
- parent_config: experiments/manifests/m638-combined-shape-source-diversity-expansion-design.json, docs/m637-combined-source7-preserving-shape-audit.md
- parent_objective: implement no-training broad source-diversity expansion for combined projected shape method
- derived_from: m638-combined-shape-source-diversity-expansion-design
- blocked_by: m638-combined-shape-source-diversity-expansion-design
- supersedes: None
- invalidates: None

## Success Criteria

- implementation writes broad expansion artifacts
- selected source rows include M627 trust-primary non-collision rows
- real run preserves trust limits
- summary reports accepted source rows physical pairs left seeds surfaces targets and variants
- summary classifies target-corpus admission candidate using pre-registered thresholds
- research validation passes

## Failure Criteria

- implementation changes thresholds
- implementation starts training
- implementation runs PPO
- implementation promotes checkpoint
- implementation counts collision-primary rows toward admission
- implementation omits source-level diversity
- implementation treats candidate count as source diversity

## Evidence Gates

- select M627 trust-primary non-collision near-miss sources
- run combined projected shape grids over expanded source set
- preserve trust limits and target thresholds
- write source-level diversity summary
- classify whether result is target-corpus admission candidate
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen trust regions
- do not lower target thresholds
- do not count collision-primary rows toward source-diversity admission
- do not treat candidate count as source diversity
- do not admit optimizer training directly

## Failure Taxonomy

- none

## Scoreboard

- milestone: m639-combined-shape-source-diversity-expansion-implementation
- type: infrastructure
- checkpoint: runs/m639_combined_shape_source_diversity_expansion/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_shape_source_diversity_expansion_pass_admit_corpus_design
- reason: M639 accepts all 9 trust-primary non-collision sources across 8 physical pairs 6 left seeds 2 surfaces and 3 targets while preserving trust limits

## Next Blocker

m640-source-diverse-sequence-target-corpus-design
