# m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark Research Review

## Summary

- Generated at UTC: 20260525T204227Z
- Type: gate
- Gate tier: generalization
- Promotion decision: raw_scaling_challenge_generalization_benchmark_pass_margin_only
- Decision reason: M903 raw candidates retain success termination and positive clearance on robust near-threshold and late high-energy challenge families with no success flips

## Hypothesis

Raw candidates will preserve success/termination and retain positive margin movement on robust challenge scenario families.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m902-v4-pair-delta-raw-scaling-challenge-generalization-design.md
- parent_config: configs/m451_challenge_near_threshold_robust_zero_relvel.json, configs/m451_challenge_late_high_energy_robust_zero_relvel.json, experiments/manifests/m902-v4-pair-delta-raw-scaling-challenge-generalization-design.json
- parent_objective: execute no-training challenge-family benchmark for raw scaling candidates
- derived_from: m902-v4-pair-delta-raw-scaling-challenge-generalization-design
- blocked_by: raw candidates have m121-style fresh margin evidence but no robust challenge-family evidence
- supersedes: None
- invalidates: None

## Success Criteria

- both challenge benchmarks complete
- raw success_rate_delta >= -0.01 on each family
- raw termination_rate_delta <= +0.01 on each family
- raw clearance_margin_mean_delta >= 0.0 on each family
- raw combined clearance_margin_mean_delta >= +0.001
- seed-delta audit is written
- M903 keeps PPO and promotion blocked

## Failure Criteria

- benchmark sampling fails
- raw candidates regress success or termination beyond tolerance
- raw clearance is negative on either family
- combined raw clearance is below +0.001
- M903 runs PPO or promotes

## Evidence Gates

- near-threshold robust challenge benchmark with 128 episodes
- late high-energy robust challenge benchmark with 128 episodes
- include M568, alpha_0_1 candidates, raw candidates, heuristic, and random
- success/termination non-regression versus M568 on each family
- raw clearance nonnegative on each family and combined clearance >= +0.001
- seed-delta audit after benchmarks
- no PPO or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not change thresholds after seeing challenge results
- do not treat these public challenge configs as private holdouts

## Failure Taxonomy

- behavior_regression
- metric_artifact
- scenario_sampling_failure
- objective_overfit
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark
- type: gate
- checkpoint: runs/m903_raw_scaling_challenge_seed_delta/policy_delta_summary.csv
- success_rate: 0.843750
- termination_rate: 0.156250
- clearance_margin_mean: 1.827309
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: raw_scaling_challenge_generalization_benchmark_pass_margin_only
- reason: M903 raw candidates retain success termination and positive clearance on robust near-threshold and late high-energy challenge families with no success flips

## Next Blocker

Raw scaling candidates have not yet run robust challenge-family generalization benchmarks
