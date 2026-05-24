# m641-source-diverse-sequence-target-corpus-implementation Research Review

## Summary

- Generated at UTC: 20260524T122647Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_diverse_sequence_target_corpus_pass_admit_exact_sanity
- Decision reason: M641 writes a 431-row source-balanced CSV and NPZ sequence target corpus across 9 sources 8 physical pairs 6 left seeds 2 surfaces and 3 targets while keeping actor training blocked

## Hypothesis

M639 accepted sequence candidates can be capped and materialized into a source-balanced sequence target corpus with heldout-source splits.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m639_combined_shape_source_diversity_expansion/accepted_expanded_sequences.csv, runs/m639_combined_shape_source_diversity_expansion/source_recovery_summary.csv, docs/m640-source-diverse-sequence-target-corpus-design.md
- parent_config: experiments/manifests/m640-source-diverse-sequence-target-corpus-design.json
- parent_objective: implement source-balanced capped sequence target corpus from M639 accepted candidates
- derived_from: m640-source-diverse-sequence-target-corpus-design
- blocked_by: m640-source-diverse-sequence-target-corpus-design
- supersedes: None
- invalidates: None

## Success Criteria

- balanced corpus CSV is written
- balanced sequence target NPZ is written
- selected sources physical pairs left seeds surfaces targets and variants meet M640 thresholds
- source-balanced weights are written
- training PPO and promotion remain blocked
- research validation passes

## Failure Criteria

- implementation starts training
- implementation writes no NPZ target sequences
- implementation lets one source exceed cap
- implementation uses raw candidate count as weight
- implementation omits source-heldout split

## Evidence Gates

- cap selected rows per source grid family and sequence length
- write source-balanced CSV and NPZ corpus
- write source balance summaries and top-k diagnostics
- preserve source surface target and variant diversity
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not feed metadata labels into actor inputs
- do not use raw candidate count as corpus weight
- do not split the same physical pair across train and validation
- do not write CSV-only corpus if NPZ materialization fails

## Failure Taxonomy

- none

## Scoreboard

- milestone: m641-source-diverse-sequence-target-corpus-implementation
- type: infrastructure
- checkpoint: runs/m641_source_diverse_sequence_target_corpus/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_sequence_target_corpus_pass_admit_exact_sanity
- reason: M641 writes a 431-row source-balanced CSV and NPZ sequence target corpus across 9 sources 8 physical pairs 6 left seeds 2 surfaces and 3 targets while keeping actor training blocked

## Next Blocker

m642-sequence-corpus-exact-objective-sanity
