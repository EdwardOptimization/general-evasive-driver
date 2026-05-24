# m624-longer-low-amplitude-sequence-miner Research Review

## Summary

- Generated at UTC: 20260524T102310Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: longer_low_amplitude_sequence_miner_diagnostic_negative_admit_audit
- Decision reason: M624 increases accepted candidates from 189 to 607 and selected margin mean to 0.068523 but source-level accepted diversity remains 6 rows 5 pairs and 4 left seeds

## Hypothesis

Adding K=7 and intermediate low-amplitude steer deltas may recover additional source-diverse accepted sequences while preserving M621 trust regions and target thresholds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv, runs/m621_tier_aware_sequence_target_miner/summary.json, docs/m623-longer-low-amplitude-sequence-design.md
- parent_config: experiments/manifests/m623-longer-low-amplitude-sequence-design.json, docs/m622-tier-aware-sequence-candidate-audit.md
- parent_objective: run K=3/5/7 low-amplitude sequence diagnostic without changing thresholds or trust regions
- derived_from: m623-longer-low-amplitude-sequence-design
- blocked_by: m623-longer-low-amplitude-sequence-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary records diagnostic_only true actor_parameters_changed false ppo_used false promoted false optimizer_admission false
- sequence_lengths includes 3 5 and 7
- accepted_candidate_sequences.csv is written
- accepted selected sequence diversity and accepted candidate diversity are reported
- result is compared against M621 in the milestone doc
- research validation passes

## Failure Criteria

- miner trains a model
- miner runs PPO
- miner promotes a checkpoint
- miner lowers target thresholds
- miner widens trust regions
- miner omits M621 comparison

## Evidence Gates

- run K=3/5/7 sequence mining on M616 expanded source rows
- write tier-aware accepted_candidate_sequences.csv
- compare source-level diversity against M621
- keep target thresholds unchanged
- keep action trust regions unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen action trust regions
- do not lower target thresholds
- do not claim optimizer admission before a later audit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m624-longer-low-amplitude-sequence-miner
- type: infrastructure
- checkpoint: runs/m624_longer_low_amplitude_sequence_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: longer_low_amplitude_sequence_miner_diagnostic_negative_admit_audit
- reason: M624 increases accepted candidates from 189 to 607 and selected margin mean to 0.068523 but source-level accepted diversity remains 6 rows 5 pairs and 4 left seeds

## Next Blocker

m625-longer-low-amplitude-sequence-audit
