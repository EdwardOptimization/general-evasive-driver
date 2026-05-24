# m666-normal-success-boundary-source-mining-design Research Review

## Summary

- Generated at UTC: 20260524T142328Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: normal_success_boundary_source_mining_design_admit_m667
- Decision reason: M666 designs normal-success near-boundary source mining with normal prepass margin bands wrong-history pairing gates and negative-result taxonomy

## Hypothesis

Filtering left snapshots by normal-history success and positive near-boundary margin before wrong-history pairing will produce usable action/outcome-critical wrong-history rows that M664 missed.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m664_action_critical_wrong_history_source_miner/summary.json, runs/m664_action_critical_wrong_history_source_miner/candidate_scores.csv, docs/m665-action-critical-source-miner-audit.md
- parent_config: experiments/manifests/m665-action-critical-source-miner-audit.json
- parent_objective: design normal-success near-boundary source mining after M664 action-gap/outcome-gap split
- derived_from: m665-action-critical-source-miner-audit
- blocked_by: m665-action-critical-source-miner-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines normal-success source filter
- design defines positive margin bands and window diagnostics
- design defines wrong-history pairing and acceptance thresholds
- design defines required artifacts and negative-result interpretation
- research validation passes

## Failure Criteria

- design allows normal-failed preferred branches
- design omits margin-band diagnostics
- design weakens action/outcome thresholds
- design admits actor coupling or PPO before source evidence exists

## Evidence Gates

- design normal-history success and margin-band source filter
- preserve action/outcome wrong-history acceptance thresholds
- separate early-safe, near-boundary, and already-failed source windows
- keep actor coupling, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not accept normal-failed rows as preferred branches
- do not weaken M664 action/outcome thresholds
- do not use hidden parameters or labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m666-normal-success-boundary-source-mining-design
- type: infrastructure
- checkpoint: docs/m666-normal-success-boundary-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: normal_success_boundary_source_mining_design_admit_m667
- reason: M666 designs normal-success near-boundary source mining with normal prepass margin bands wrong-history pairing gates and negative-result taxonomy

## Next Blocker

m667-normal-success-boundary-source-miner-implementation
