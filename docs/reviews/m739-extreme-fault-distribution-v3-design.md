# m739-extreme-fault-distribution-v3-design Research Review

## Summary

- Generated at UTC: 20260524T221947Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: extreme_fault_distribution_v3_design_admit_m740
- Decision reason: M739 defines v3 fault taxonomy config matched counterfactual gates public holdout policy and current-model versus future-only claim boundary before a no-training data wave

## Hypothesis

A broader extreme-fault distribution with matched counterfactuals is needed before the next objective branch because current public positives and hard negatives are too narrow.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m738-sequence-outcome-corpus-export-audit.md, docs/m737-sequence-outcome-corpus-export-implementation.md, runs/m737_sequence_outcome_corpus_export/summary.json, configs/extreme_fault_coverage_v2_scenarios.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_config: experiments/manifests/m738-sequence-outcome-corpus-export-audit.json
- parent_objective: design broader extreme-fault scenario distribution after M737 hard-negative sparsity and user coverage concern
- derived_from: m738-sequence-outcome-corpus-export-audit
- blocked_by: m738-sequence-outcome-corpus-export-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M739 defines the v3 fault taxonomy
- M739 separates current-model proxy faults from four-wheel-required faults
- M739 defines scenario randomization and fault-onset timing
- M739 defines public and holdout split policy
- M739 defines source-balance sentinel action and outcome gates
- M739 blocks actor update PPO and promotion
- M739 admits only a no-training M740 implementation

## Failure Criteria

- design claims true single-wheel physics from current single-track proxies
- design omits matched counterfactual pairing
- design omits public and holdout split policy
- design admits PPO or checkpoint promotion
- design changes actor input contract

## Evidence Gates

- M739 defines current-model proxy and four-wheel-required fault taxonomy
- M739 defines matched counterfactual source generation
- M739 defines public and holdout split policy
- M739 defines sequence intervention and outcome gates
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current single-track proxies
- do not collapse public and holdout distributions

## Failure Taxonomy

- none

## Scoreboard

- milestone: m739-extreme-fault-distribution-v3-design
- type: infrastructure
- checkpoint: docs/m739-extreme-fault-distribution-v3-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_distribution_v3_design_admit_m740
- reason: M739 defines v3 fault taxonomy config matched counterfactual gates public holdout policy and current-model versus future-only claim boundary before a no-training data wave

## Next Blocker

m740-extreme-fault-distribution-v3-implementation
