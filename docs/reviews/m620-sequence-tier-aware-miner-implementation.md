# m620-sequence-tier-aware-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T100220Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: sequence_tier_aware_miner_pass_admit_rerun
- Decision reason: M620 propagates source-tier metadata writes accepted_candidate_sequences.csv and shows 189 accepted candidates across only 5 physical pairs and 4 left seeds so optimizer admission remains blocked

## Hypothesis

Adding source-tier propagation and accepted candidate-set artifacts will make sequence target evidence auditable without changing model behavior or target thresholds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m617_expanded_sequence_target_miner/sequence_candidates.csv, runs/m617_expanded_sequence_target_miner/accepted_sequences.csv, docs/m619-expanded-sequence-diversity-design.md
- parent_config: experiments/manifests/m619-expanded-sequence-diversity-design.json, docs/m618-expanded-sequence-target-mining-audit.md
- parent_objective: implement source-tier metadata propagation and accepted candidate-set artifacts for sequence target miner
- derived_from: m619-expanded-sequence-diversity-design
- blocked_by: m619-expanded-sequence-diversity-design
- supersedes: None
- invalidates: None

## Success Criteria

- sequence_candidates accepted_sequences and unaccepted_rows preserve source_tier metadata when present
- accepted_candidate_sequences.csv is written with all accepted candidates
- summary includes accepted_candidate_diversity and accepted candidate counts by family tier and sequence length
- older source files without tier metadata still work
- focused tests and research validation pass

## Failure Criteria

- implementation changes actor inputs
- implementation trains a model
- implementation runs PPO
- implementation changes target acceptance thresholds
- implementation breaks older source files

## Evidence Gates

- propagate optional source metadata columns into sequence outputs
- write accepted_candidate_sequences.csv
- summarize accepted candidate-set diversity separately from selected sequence diversity
- preserve backward compatibility for older source rows
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not change actor inputs
- do not lower target acceptance thresholds
- do not widen action trust regions

## Failure Taxonomy

- none

## Scoreboard

- milestone: m620-sequence-tier-aware-miner-implementation
- type: infrastructure
- checkpoint: runs/m620_tier_aware_sequence_target_miner_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_tier_aware_miner_pass_admit_rerun
- reason: M620 propagates source-tier metadata writes accepted_candidate_sequences.csv and shows 189 accepted candidates across only 5 physical pairs and 4 left seeds so optimizer admission remains blocked

## Next Blocker

m621-tier-aware-sequence-target-miner-rerun
