# m609-boundary-conditioned-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T085759Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: boundary_conditioned_source_miner_partial_admit_limited_target_smoke
- Decision reason: M609 finds 17 near-boundary source rows across 16 physical pairs but misses the 24-row desired diversity threshold; limited diagnostic target search admitted but optimizer admission remains blocked

## Hypothesis

Scanning the full reconstructable M604 belief-only source pool with baseline boundary/risk rollouts will identify source-diverse near-boundary rows suitable for a second grounded target miner.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv, docs/m608-boundary-conditioned-grounded-source-design.md
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json, experiments/manifests/m608-boundary-conditioned-grounded-source-design.json
- parent_objective: implement boundary/risk-conditioned source miner before rerunning target search
- derived_from: m608-boundary-conditioned-grounded-source-design
- blocked_by: m608-boundary-conditioned-grounded-source-design
- supersedes: None
- invalidates: None

## Success Criteria

- source_rollouts.csv is written
- boundary_source_rows.csv is written
- rejected_far_rows.csv is written
- summary reports accepted boundary rows and diversity counts
- summary records actor_parameters_changed false ppo_used false promoted false
- research validation and focused tests pass

## Failure Criteria

- miner trains any model
- miner runs PPO
- miner emits action targets
- miner omits rejected or far rows
- miner promotes a checkpoint

## Evidence Gates

- write source_rollouts.csv
- write boundary_source_rows.csv
- write rejected_far_rows.csv
- write summary with source diversity
- prove no model weights are changed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not create action targets
- do not use belief-only gaps as action labels
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m609-boundary-conditioned-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m609_boundary_conditioned_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_conditioned_source_miner_partial_admit_limited_target_smoke
- reason: M609 finds 17 near-boundary source rows across 16 physical pairs but misses the 24-row desired diversity threshold; limited diagnostic target search admitted but optimizer admission remains blocked

## Next Blocker

m610-boundary-conditioned-grounded-target-miner
