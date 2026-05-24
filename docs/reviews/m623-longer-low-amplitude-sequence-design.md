# m623-longer-low-amplitude-sequence-design Research Review

## Summary

- Generated at UTC: 20260524T101644Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: longer_low_amplitude_sequence_design_admit_m624
- Decision reason: M623 designs a K3/5/7 low-amplitude diagnostic with intermediate steer deltas while preserving trust regions target thresholds and no-training constraints

## Hypothesis

A longer K=7 low-amplitude sequence diagnostic may recover additional source-diverse accepted sequences without widening action trust regions or lowering target thresholds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m621_tier_aware_sequence_target_miner/summary.json, runs/m621_tier_aware_sequence_target_miner/accepted_candidate_sequences.csv, docs/m622-tier-aware-sequence-candidate-audit.md
- parent_config: experiments/manifests/m622-tier-aware-sequence-candidate-audit.json, docs/m621-tier-aware-sequence-target-miner-rerun.md
- parent_objective: design longer low-amplitude sequence diagnostic after candidate-level diversity remains source-narrow
- derived_from: m622-tier-aware-sequence-candidate-audit
- blocked_by: m622-tier-aware-sequence-candidate-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies K=7 candidate families and deltas
- design preserves all M621 trust-region and target thresholds
- design defines source-level success criteria and candidate-level diagnostics separately
- design keeps optimizer admission training PPO and promotion blocked
- research validation passes

## Failure Criteria

- design starts training
- design widens trust regions
- design lowers target thresholds
- design claims optimizer admission from M621 candidate rows
- design omits comparison to M621

## Evidence Gates

- define K=7 low-amplitude sequence candidate policy
- keep action trust regions unchanged
- keep target acceptance thresholds unchanged
- define comparison against M621 K=3/5 baseline
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not widen action trust regions
- do not lower target thresholds
- do not treat candidate rows as independent source diversity

## Failure Taxonomy

- none

## Scoreboard

- milestone: m623-longer-low-amplitude-sequence-design
- type: infrastructure
- checkpoint: docs/m623-longer-low-amplitude-sequence-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: longer_low_amplitude_sequence_design_admit_m624
- reason: M623 designs a K3/5/7 low-amplitude diagnostic with intermediate steer deltas while preserving trust regions target thresholds and no-training constraints

## Next Blocker

m624-longer-low-amplitude-sequence-miner
