# m622-tier-aware-sequence-candidate-audit Research Review

## Summary

- Generated at UTC: 20260524T100834Z
- Type: gate
- Gate tier: process
- Promotion decision: tier_aware_candidate_audit_admit_longer_sequence_design
- Decision reason: M622 audits 189 accepted candidate rows as useful family diversity but not source diversity and admits K7 low-amplitude sequence design without optimizer admission

## Hypothesis

M621 candidate-set artifacts will show useful family diversity but insufficient source-level diversity; the audit should decide whether to run a longer K=7 low-amplitude diagnostic or expand source rows again.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m621_tier_aware_sequence_target_miner/summary.json, runs/m621_tier_aware_sequence_target_miner/accepted_candidate_sequences.csv, runs/m621_tier_aware_sequence_target_miner/accepted_sequences.csv, docs/m621-tier-aware-sequence-target-miner-rerun.md
- parent_config: experiments/manifests/m621-tier-aware-sequence-target-miner-rerun.json, docs/m620-sequence-tier-aware-miner-implementation.md
- parent_objective: audit tier-aware accepted candidate-set evidence before longer sequence families or optimizer design
- derived_from: m621-tier-aware-sequence-target-miner-rerun
- blocked_by: m621-tier-aware-sequence-target-miner-rerun
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes accepted candidate family tier and sequence-length diversity
- audit explicitly distinguishes candidate-level and source-level diversity
- audit blocks optimizer admission if source-level diversity remains insufficient
- audit selects the next no-training branch
- research validation passes

## Failure Criteria

- audit starts training
- audit promotes a checkpoint
- audit treats correlated candidate rows as independent source rows
- audit ignores source-tier distribution
- audit changes target thresholds or trust regions

## Evidence Gates

- audit accepted candidate-set diversity
- separate source-level diversity from candidate-level diversity
- verify optimizer admission remains blocked unless source-level thresholds pass
- choose next no-training branch

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not treat 189 candidate rows as independent source diversity
- do not lower target thresholds
- do not widen trust regions

## Failure Taxonomy

- none

## Scoreboard

- milestone: m622-tier-aware-sequence-candidate-audit
- type: gate
- checkpoint: docs/m622-tier-aware-sequence-candidate-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: tier_aware_candidate_audit_admit_longer_sequence_design
- reason: M622 audits 189 accepted candidate rows as useful family diversity but not source diversity and admits K7 low-amplitude sequence design without optimizer admission

## Next Blocker

m623-longer-low-amplitude-sequence-design
