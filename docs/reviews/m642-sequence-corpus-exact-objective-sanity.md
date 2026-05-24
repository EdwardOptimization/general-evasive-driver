# m642-sequence-corpus-exact-objective-sanity Research Review

## Summary

- Generated at UTC: 20260524T123206Z
- Type: gate
- Gate tier: proof
- Promotion decision: sequence_corpus_exact_sanity_pass_admit_bc_v2_design
- Decision reason: M642 verifies the M641 corpus has 431 nonzero masked target rows balanced source weights zero outside-mask padding and close train/source-heldout objective scales

## Hypothesis

The M641 source-balanced sequence corpus is exact-objective usable: target sequences differ meaningfully from base sequences while loss mass remains source-balanced and auditable by split.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/summary.json, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m641_source_diverse_sequence_target_corpus/source_balance_summary.csv, docs/m641-source-diverse-sequence-target-corpus-implementation.md
- parent_config: experiments/manifests/m641-source-diverse-sequence-target-corpus-implementation.json
- parent_objective: check whether the M641 source-balanced sequence target corpus has usable exact objective geometry before any actor update
- derived_from: m641-source-diverse-sequence-target-corpus-implementation
- blocked_by: m641-source-diverse-sequence-target-corpus-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- NPZ and metadata load successfully
- weighted source contributions are finite and balanced
- target/base sequence deltas are nonzero and bounded by recorded masks
- train and source-heldout validation summaries are written separately
- no actor parameters are changed
- research validation passes

## Failure Criteria

- NPZ cannot be loaded
- metadata and NPZ row counts mismatch
- source weights are not balanced
- target/base sequence deltas are all zero or non-finite
- split-specific summaries are missing
- any optimizer or actor update is started

## Evidence Gates

- load the M641 NPZ and metadata without mutation
- compute target versus base sequence distances
- report source-balanced loss contributions
- report train and source-heldout validation splits separately
- confirm no actor parameters change and no training starts

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not change actor inputs
- do not use source or target metadata as actor observations
- do not report aggregate loss without source-balanced and split-specific breakdowns

## Failure Taxonomy

- none

## Scoreboard

- milestone: m642-sequence-corpus-exact-objective-sanity
- type: gate
- checkpoint: runs/m642_sequence_corpus_exact_objective_sanity/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_corpus_exact_sanity_pass_admit_bc_v2_design
- reason: M642 verifies the M641 corpus has 431 nonzero masked target rows balanced source weights zero outside-mask padding and close train/source-heldout objective scales

## Next Blocker

m643-source-balanced-bc-v2-objective-design
