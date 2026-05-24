# m621-tier-aware-sequence-target-miner-rerun Research Review

## Summary

- Generated at UTC: 20260524T100640Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: tier_aware_sequence_rerun_pass_admit_candidate_audit
- Decision reason: M621 reproduces M617 selected-sequence metrics and writes 189 accepted candidate rows with tier metadata while source-level diversity remains 5 physical pairs and 4 left seeds

## Hypothesis

A formal rerun with the M620 tier-aware miner will reproduce M617 selected-sequence results while adding accepted candidate-set and source-tier summaries needed for the next audit.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv, docs/m620-sequence-tier-aware-miner-implementation.md
- parent_config: experiments/manifests/m620-sequence-tier-aware-miner-implementation.json, docs/m619-expanded-sequence-diversity-design.md
- parent_objective: rerun sequence target miner with tier-aware artifacts after M620 implementation
- derived_from: m620-sequence-tier-aware-miner-implementation
- blocked_by: m620-sequence-tier-aware-miner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- accepted selected sequence count matches the M617 diagnostic result within deterministic tolerance
- accepted_candidate_sequences.csv is written
- summary includes accepted_candidate_diversity and accepted_candidate_counts_by_tier
- accepted_sequences.csv and unaccepted_rows.csv include source_tier
- research validation passes

## Failure Criteria

- rerun changes model weights
- rerun changes target thresholds or trust regions
- rerun omits accepted candidate-set artifact
- rerun loses source-tier metadata
- rerun makes optimizer admission claim

## Evidence Gates

- write accepted_candidate_sequences.csv
- write tier-aware accepted_sequences.csv
- write tier-aware unaccepted_rows.csv
- record accepted candidate-set diversity
- keep target thresholds and trust regions unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not lower target acceptance thresholds
- do not widen action trust regions
- do not treat candidate-level rows as independent source diversity

## Failure Taxonomy

- none

## Scoreboard

- milestone: m621-tier-aware-sequence-target-miner-rerun
- type: infrastructure
- checkpoint: runs/m621_tier_aware_sequence_target_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: tier_aware_sequence_rerun_pass_admit_candidate_audit
- reason: M621 reproduces M617 selected-sequence metrics and writes 189 accepted candidate rows with tier metadata while source-level diversity remains 5 physical pairs and 4 left seeds

## Next Blocker

m622-tier-aware-sequence-candidate-audit
