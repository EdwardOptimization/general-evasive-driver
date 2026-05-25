# m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark Research Review

## Summary

- Generated at UTC: 20260525T203253Z
- Type: gate
- Gate tier: generalization
- Promotion decision: raw_scaling_fresh_generalization_benchmark_pass_margin_only
- Decision reason: M900 raw candidates retain success termination and exceed fresh clearance threshold with about 0.00325 margin lift but no success flips

## Hypothesis

Raw candidates will retain success/termination and show larger clearance movement than alpha_0_1 on a fresh public diagnostic distribution.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m899-v4-pair-delta-raw-scaling-fresh-generalization-design.md
- parent_config: configs/m121_human_view_zero_obstacle_relvel.json, experiments/manifests/m899-v4-pair-delta-raw-scaling-fresh-generalization-design.json
- parent_objective: execute no-training fresh/generalization benchmark for raw scaling candidates
- derived_from: m899-v4-pair-delta-raw-scaling-fresh-generalization-design
- blocked_by: raw candidates have public proof retention but no fresh/generalization benchmark evidence
- supersedes: None
- invalidates: None

## Success Criteria

- both benchmark runs complete
- raw success_rate_delta >= -0.005 versus M568
- raw termination_rate_delta <= +0.005 versus M568
- raw clearance_margin_mean_delta >= +0.002 versus M568
- seed-delta audit is written
- M900 keeps PPO and promotion blocked

## Failure Criteria

- benchmark sampling fails
- raw candidates regress success or termination beyond tolerance
- raw clearance delta is below +0.002 and seed deltas show no useful events
- M900 runs PPO or promotes

## Evidence Gates

- benchmark seeds 9705 and 9706 over 256 episodes each
- include M568, alpha_0_1 candidates, raw candidates, heuristic, and random
- success/termination non-regression versus M568
- raw clearance delta >= +0.002 over combined fresh benchmark
- seed-delta audit after benchmark
- no PPO or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not change benchmark thresholds after seeing results
- do not treat this public fresh benchmark as a private holdout

## Failure Taxonomy

- behavior_regression
- objective_overfit
- metric_artifact
- scenario_sampling_failure
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark
- type: gate
- checkpoint: runs/m900_raw_scaling_fresh_generalization_seed_delta/policy_delta_summary.csv
- success_rate: 0.761719
- termination_rate: 0.238281
- clearance_margin_mean: 1.486368
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: raw_scaling_fresh_generalization_benchmark_pass_margin_only
- reason: M900 raw candidates retain success termination and exceed fresh clearance threshold with about 0.00325 margin lift but no success flips

## Next Blocker

Raw scaling candidates have not yet run the pre-registered fresh/generalization benchmark
