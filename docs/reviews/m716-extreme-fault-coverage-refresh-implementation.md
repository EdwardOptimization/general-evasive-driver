# m716-extreme-fault-coverage-refresh-implementation Research Review

## Summary

- Generated at UTC: 20260524T194139Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: cross_fault_reset_only_not_source_positive
- Decision reason: M716 runs 16896 scenarios and 4096 matched pairs with 58 reset-only rows but 0 wrong-history action-critical rows so source export actor update PPO and promotion remain blocked

## Hypothesis

The v2 extreme-fault coverage wave will expose more matched-history-sensitive cases than M704/M707 by broadening fault families, severity levels, surprise activations, and current-model proxy combinations.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m715-extreme-fault-coverage-refresh-design.md, configs/extreme_fault_coverage_v2_scenarios.json
- parent_config: experiments/manifests/m715-extreme-fault-coverage-refresh-design.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: generate a broader no-training extreme-fault coverage discovery wave
- derived_from: m715-extreme-fault-coverage-refresh-design
- blocked_by: m715-extreme-fault-coverage-refresh-design
- supersedes: None
- invalidates: None

## Success Criteria

- full run writes runs/m716_extreme_fault_coverage_refresh/summary.json
- actor_parameters_changed is false
- training_started is false or absent
- ppo_used is false
- promoted is false
- result_class is recorded
- failure taxonomy and next blocker are documented

## Failure Criteria

- runner fails to load the v2 config
- actor inputs or observation shape change
- run claims true wheel-asymmetric physics from current-model proxies
- run omits fault-family and severity summaries
- implementation promotes a checkpoint or admits PPO

## Evidence Gates

- runner uses configs/extreme_fault_coverage_v2_scenarios.json
- run is no-training no-PPO no-promotion with actor checksum unchanged
- summary reports scenario_count snapshot_count matched_pair_count accepted/reset/wrong rows
- fault-family and severity summaries are written
- current-model proxy and future-only fidelity boundaries are preserved
- result class determines whether to export source rows, return to actor-head objective design, or design higher-fidelity dynamics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add fault labels hidden params or oracle labels to actor observations
- do not claim proxy faults are faithful single-wheel physics
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not tune thresholds after seeing the full run without registering a new manifest

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m716-extreme-fault-coverage-refresh-implementation
- type: infrastructure
- checkpoint: runs/m716_extreme_fault_coverage_refresh/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_reset_only_not_source_positive
- reason: M716 runs 16896 scenarios and 4096 matched pairs with 58 reset-only rows but 0 wrong-history action-critical rows so source export actor update PPO and promotion remain blocked

## Next Blocker

m717-extreme-fault-coverage-refresh-audit
