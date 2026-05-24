# m740-extreme-fault-distribution-v3-implementation Research Review

## Summary

- Generated at UTC: 20260524T222902Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: cross_fault_reset_only
- Decision reason: M740 runs 16896 v3 scenarios and 8192 matched pairs producing 744 reset-only rows but 0 wrong-history action-critical rows so PPO and objective work remain blocked pending audit

## Hypothesis

The v3 extreme-fault distribution will produce broader action or outcome-sensitive command-response self-ID rows than the M737 public corpus alone.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m739-extreme-fault-distribution-v3-design.md, configs/extreme_fault_distribution_v3_scenarios.json, docs/m738-sequence-outcome-corpus-export-audit.md
- parent_config: experiments/manifests/m739-extreme-fault-distribution-v3-design.json
- parent_objective: run no-training v3 extreme-fault matched counterfactual data wave
- derived_from: m739-extreme-fault-distribution-v3-design
- blocked_by: m739-extreme-fault-distribution-v3-design
- supersedes: None
- invalidates: None

## Success Criteria

- M740 validates v3 config with a smoke run or registered run
- M740 runs the no-training v3 data wave
- M740 writes scenario matched-pair accepted rejected and summary artifacts
- M740 reports source diversity reset wrong-history action and outcome metrics separately
- M740 records current-model versus future-only claim boundary
- actor checksum remains unchanged
- no actor training PPO or promotion occurs

## Failure Criteria

- v3 config fails to load
- source generation diversity gates fail without classification
- future-only faults are counted as current-model evidence
- actor input contract changes
- optimizer training PPO or checkpoint promotion starts

## Evidence Gates

- M740 uses v3 fault distribution config
- M740 reports source generation and diversity metrics
- M740 separates reset wrong-history action and outcome evidence
- M740 respects current-model versus future-only claim boundary
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current single-track proxies
- do not lower gates after seeing M740 output

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m740-extreme-fault-distribution-v3-implementation
- type: infrastructure
- checkpoint: runs/m740_extreme_fault_distribution_v3/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_reset_only
- reason: M740 runs 16896 v3 scenarios and 8192 matched pairs producing 744 reset-only rows but 0 wrong-history action-critical rows so PPO and objective work remain blocked pending audit

## Next Blocker

m741-extreme-fault-distribution-v3-audit
