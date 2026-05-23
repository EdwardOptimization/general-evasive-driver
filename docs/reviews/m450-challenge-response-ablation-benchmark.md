# m450-challenge-response-ablation-benchmark Research Review

## Summary

- Generated at UTC: 20260523T193952Z
- Type: gate
- Gate tier: generalization
- Promotion decision: reject_sampling_failure_admit_config_robustness_repair
- Decision reason: M450 ablation benchmark fails before policy evaluation because both challenge configs cannot sample seed 9900 scenarios

## Hypothesis

Even if recent checkpoint candidates are indistinguishable, the challenge configs may still reveal dependence on recurrent response/action history through M399 ablations.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m449_near_threshold_benchmark_seed9800/episodes.csv, runs/m449_late_high_energy_benchmark_seed9800/episodes.csv
- parent_config: configs/m449_challenge_near_threshold_zero_relvel.json, configs/m449_challenge_late_high_energy_zero_relvel.json, experiments/manifests/m449-challenge-distribution-config-implementation.json
- parent_objective: challenge response/history ablation benchmark
- derived_from: m449-challenge-distribution-config-implementation
- blocked_by: m449-challenge-distribution-config-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- near and late benchmarks complete
- normal versus ablated success and margin deltas are documented
- decision states whether the challenge configs are useful self-ID diagnostics
- no checkpoint is promoted

## Failure Criteria

- benchmark fails
- ablation results are used for promotion
- actor contract changes
- no decision is made about diagnostic usefulness

## Evidence Gates

- near-threshold response ablation benchmark
- late high-energy response ablation benchmark
- normal versus reset and zero-response comparison
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not tune checkpoints from ablation results

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m450-challenge-response-ablation-benchmark
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_sampling_failure_admit_config_robustness_repair
- reason: M450 ablation benchmark fails before policy evaluation because both challenge configs cannot sample seed 9900 scenarios

## Next Blocker

m451-challenge-config-sampling-robustness-repair
