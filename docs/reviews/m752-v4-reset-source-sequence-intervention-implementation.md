# m752-v4-reset-source-sequence-intervention-implementation Research Review

## Summary

- Generated at UTC: 20260524T233442Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: v4_reset_sequence_outcome_positive
- Decision reason: M752 runs source-balanced v4 reset-source sequence interventions with 1213 outcome-critical rows across 27 seeds and 17 fault-family pairs with zero sentinel false positives

## Hypothesis

Persistent sequence-level command-response interventions over M749 v4 reset-only rows will expose outcome sensitivity.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m751-v4-reset-source-sequence-intervention-design.md, runs/m749_extreme_fault_distribution_v4/summary.json, runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv, runs/m749_extreme_fault_distribution_v4/rejected_rows.csv
- parent_config: experiments/manifests/m751-v4-reset-source-sequence-intervention-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: run no-training source-balanced sequence-level interventions over M749 v4 reset-only rows
- derived_from: m751-v4-reset-source-sequence-intervention-design
- blocked_by: m751-v4-reset-source-sequence-intervention-design
- supersedes: None
- invalidates: None

## Success Criteria

- M752 implements v4 source adapter and focused tests
- M752 runs smoke and registered no-training sequence intervention wave
- M752 writes source rollout critical sentinel rejected and summary artifacts
- M752 reports source-balance action outcome and sentinel metrics separately
- actor checksum remains unchanged
- no training PPO actor update or promotion occurs

## Failure Criteria

- runner mutates actor observations with hidden fault labels
- runner omits sentinel rows
- runner combines action-only and outcome-positive claims
- runner changes actor input contract
- runner starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- M752 adapts M749 reset-only rows into source-balanced sequence sources
- M752 includes sentinel rows from history-insensitive rejected rows
- M752 reports action outcome and sentinel metrics separately
- M752 keeps actor checksum and input contract unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as wrong-history proof
- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current proxy faults

## Failure Taxonomy

- none

## Scoreboard

- milestone: m752-v4-reset-source-sequence-intervention-implementation
- type: infrastructure
- checkpoint: runs/m752_v4_reset_source_sequence_intervention/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_reset_sequence_outcome_positive
- reason: M752 runs source-balanced v4 reset-source sequence interventions with 1213 outcome-critical rows across 27 seeds and 17 fault-family pairs with zero sentinel false positives

## Next Blocker

m753-v4-reset-source-sequence-intervention-audit
