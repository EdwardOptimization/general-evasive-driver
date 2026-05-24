# m625-longer-low-amplitude-sequence-audit Research Review

## Summary

- Generated at UTC: 20260524T102544Z
- Type: gate
- Gate tier: process
- Promotion decision: longer_low_amplitude_sequence_audit_admit_trust_geometry_design
- Decision reason: M625 classifies M624 as positive for longer-prefix utility but negative for source diversity and admits no-training near-miss trust-geometry design

## Hypothesis

M624 improves accepted candidate count and selected margin but not source-level diversity; the audit should classify this as diagnostic negative for source diversity and choose whether to inspect near-miss trust geometry or expand source mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m624_longer_low_amplitude_sequence_miner/summary.json, runs/m624_longer_low_amplitude_sequence_miner/accepted_candidate_sequences.csv, runs/m624_longer_low_amplitude_sequence_miner/unaccepted_rows.csv, docs/m624-longer-low-amplitude-sequence-miner.md
- parent_config: experiments/manifests/m624-longer-low-amplitude-sequence-miner.json, docs/m623-longer-low-amplitude-sequence-design.md
- parent_objective: audit K=7 low-amplitude sequence diagnostic after candidate count improves but source diversity does not
- derived_from: m624-longer-low-amplitude-sequence-miner
- blocked_by: m624-longer-low-amplitude-sequence-miner
- supersedes: None
- invalidates: None

## Success Criteria

- audit compares M624 to M621 on selected and candidate source diversity
- audit classifies whether K=7 solved source-level diversity
- audit blocks optimizer admission if source-level diversity remains insufficient
- audit selects a next no-training branch
- research validation passes

## Failure Criteria

- audit starts training
- audit promotes a checkpoint
- audit treats 607 candidate rows as independent source examples
- audit ignores near-miss trust-region rejections
- audit changes thresholds or trust regions

## Evidence Gates

- compare M624 against M621
- audit source-level diversity versus candidate-level count
- verify optimizer admission remains blocked
- choose next no-training branch

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not treat candidate-level count as source diversity
- do not widen trust regions
- do not lower target thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m625-longer-low-amplitude-sequence-audit
- type: gate
- checkpoint: docs/m625-longer-low-amplitude-sequence-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: longer_low_amplitude_sequence_audit_admit_trust_geometry_design
- reason: M625 classifies M624 as positive for longer-prefix utility but negative for source diversity and admits no-training near-miss trust-geometry design

## Next Blocker

m626-near-miss-trust-geometry-design
