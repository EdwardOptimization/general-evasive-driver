# m722-temporal-action-boundary-outcome-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T203450Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_action_only_boundary_sparse
- Decision reason: M722 runs 128 source rows and 6984 rollout variants with 921 temporal action-critical rows but 0 outcome-critical rows so source export PPO and promotion remain blocked

## Hypothesis

A source-balanced no-training local boundary miner can convert M719 temporal command-history action deltas into outcome-critical clearance or success gaps without changing actor inputs or training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m721-temporal-action-boundary-outcome-mining-design.md, runs/m719_temporal_action_response_mismatch/summary.json, runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv, runs/m719_temporal_action_response_mismatch/source_rows.csv, runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
- parent_config: experiments/manifests/m721-temporal-action-boundary-outcome-mining-design.json, configs/extreme_fault_coverage_v2_scenarios.json
- parent_objective: implement no-training local boundary miner that converts temporal action sensitivity into closed-loop outcome-critical rows
- derived_from: m721-temporal-action-boundary-outcome-mining-design
- blocked_by: m721-temporal-action-boundary-outcome-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- M722 implements a reusable temporal action-boundary outcome miner
- M722 writes source rows candidate variants intervention rollouts accepted rows rejected rows summaries and milestone documentation
- accepted rows require normal-history viability and temporal mismatch outcome degradation
- source diversity and sentinel false-positive rates are reported
- actor checksum remains unchanged
- no training PPO actor update or promotion occurs

## Failure Criteria

- runner treats M719 action-only rows as source-positive without outcome gaps
- runner accepts rows where normal history already fails
- runner omits source diversity or sentinel false-positive reporting
- runner changes actor input contract
- runner starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- runner starts from source-balanced M719 temporal action-sensitive rows
- runner reruns scenarios in memory rather than reconstructing hidden tensors from CSV only
- local obstacle timing lateral offset footprint boundary slack and surprise fault timing perturbations are logged
- normal-history retention is required before accepting outcome-critical rows
- accepted rows require first action distance >= 0.015 and success drop or margin gap >= 0.02
- sentinel false positives are tracked
- source diversity across seeds and fault families is reported
- actor input contract remains unchanged
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim action-only rows are source-positive outcome rows
- do not mutate actor observations with hidden fault labels or oracle values
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not accept rows where normal history already fails
- do not use malformed obstacle placement or impossible scenario mutation as evidence

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m722-temporal-action-boundary-outcome-miner-implementation
- type: infrastructure
- checkpoint: runs/m722_temporal_action_boundary_outcome_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_action_only_boundary_sparse
- reason: M722 runs 128 source rows and 6984 rollout variants with 921 temporal action-critical rows but 0 outcome-critical rows so source export PPO and promotion remain blocked

## Next Blocker

m723-temporal-action-boundary-outcome-miner-audit
