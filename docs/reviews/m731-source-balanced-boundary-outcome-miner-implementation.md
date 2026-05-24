# m731-source-balanced-boundary-outcome-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T213724Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_action_only_boundary_sparse
- Decision reason: M731 fixes source selection and runs a 512-row source-balanced boundary miner with 5881 action-critical rows but only 1 accepted outcome row

## Hypothesis

M728 action-critical rows can produce outcome-critical rows when locally relocated near obstacle and terminal-margin boundaries under source-balanced selection.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m730-source-balanced-boundary-outcome-mining-design.md, docs/m729-quota-calibrated-source-balanced-temporal-wave-audit.md, runs/m728_quota_calibrated_source_balanced_temporal_wave/summary.json, runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv
- parent_config: experiments/manifests/m730-source-balanced-boundary-outcome-mining-design.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: implement and run source-balanced boundary miner from M728 action-critical rows
- derived_from: m730-source-balanced-boundary-outcome-mining-design
- blocked_by: m730-source-balanced-boundary-outcome-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- M731 implements M728 schema-compatible source loading
- M731 runs smoke and registered no-training boundary miner
- M731 writes source candidate rollout accepted rejected and summary artifacts
- M731 reports source-balance action outcome and sentinel metrics separately
- actor checksum remains unchanged
- no training PPO actor update or promotion occurs

## Failure Criteria

- runner collapses M728 rows because proposal_id is ignored
- runner omits sentinel rows
- runner combines action-only and outcome-positive claims
- runner changes actor input contract
- runner starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- loader supports M728 proposal_id selected_index schema
- source rows are selected from M728 source-balanced action-critical rows
- source-balance metrics and sentinel false positives are reported
- temporal action and outcome rows are separated
- actor checksum remains unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M728 action rows as outcome proof
- do not mutate actor observations with hidden fault labels
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not lower outcome thresholds after seeing M731 output

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m731-source-balanced-boundary-outcome-miner-implementation
- type: infrastructure
- checkpoint: runs/m731_source_balanced_boundary_outcome_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_action_only_boundary_sparse
- reason: M731 fixes source selection and runs a 512-row source-balanced boundary miner with 5881 action-critical rows but only 1 accepted outcome row

## Next Blocker

m732-source-balanced-boundary-outcome-miner-audit
