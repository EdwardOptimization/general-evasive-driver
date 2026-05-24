# m730-source-balanced-boundary-outcome-mining-design Research Review

## Summary

- Generated at UTC: 20260524T212119Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_boundary_mining_design_admit_m731
- Decision reason: M730 designs a no-training boundary miner from M728 source-balanced action rows with M728 schema loader fix normal retention sentinel and outcome gates

## Hypothesis

M728 action-critical rows may become outcome-critical if evaluated near local obstacle and terminal-margin boundaries under source-balanced selection.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m729-quota-calibrated-source-balanced-temporal-wave-audit.md, docs/m728-quota-calibrated-source-balanced-temporal-wave-implementation.md, runs/m728_quota_calibrated_source_balanced_temporal_wave/summary.json, runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv, runs/m728_quota_calibrated_source_balanced_temporal_wave/selected_pair_proposals.csv
- parent_config: experiments/manifests/m729-quota-calibrated-source-balanced-temporal-wave-audit.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: design source-balanced boundary mining from M728 action-critical rows
- derived_from: m729-quota-calibrated-source-balanced-temporal-wave-audit
- blocked_by: m729-quota-calibrated-source-balanced-temporal-wave-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M730 defines the M728 action-critical source pool
- M730 defines local boundary perturbation axes
- M730 defines normal-retention sentinel and outcome gates
- M730 blocks source export actor update PPO and promotion
- M730 admits only a no-training M731 implementation

## Failure Criteria

- design treats action rows as outcome proof
- design changes actor input contract
- design omits sentinel false-positive checks
- design admits PPO or checkpoint promotion

## Evidence Gates

- M730 starts from M728 source-balanced action-critical rows
- M730 defines boundary perturbations without actor input changes
- M730 keeps normal-history retention sentinel and source-balance checks
- M730 separates action-critical and outcome-critical claims
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use the singleton M728 outcome row as a sufficient corpus
- do not export action-only rows as outcome-positive proof
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m730-source-balanced-boundary-outcome-mining-design
- type: infrastructure
- checkpoint: docs/m730-source-balanced-boundary-outcome-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_boundary_mining_design_admit_m731
- reason: M730 designs a no-training boundary miner from M728 source-balanced action rows with M728 schema loader fix normal retention sentinel and outcome gates

## Next Blocker

m731-source-balanced-boundary-outcome-miner-implementation
