# m902-v4-pair-delta-raw-scaling-challenge-generalization-design Research Review

## Summary

- Generated at UTC: 20260525T203542Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: not_applicable
- Decision reason: M902 may only design the challenge-family benchmark. It must not run benchmark, train, run PPO, or promote.

## Hypothesis

Raw scaling should be tested on robust challenge scenario families before public-base integration, PPO, or promotion.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m901-v4-pair-delta-raw-scaling-fresh-result-audit.md, runs/m900_raw_scaling_fresh_generalization_seed_delta/policy_delta_summary.csv
- parent_config: experiments/manifests/m901-v4-pair-delta-raw-scaling-fresh-result-audit.json
- parent_objective: design no-training challenge-family generalization benchmark after M900 margin-only fresh pass
- derived_from: m901-v4-pair-delta-raw-scaling-fresh-result-audit
- blocked_by: M900 showed margin-only fresh movement on m121-style distribution but no success flips
- supersedes: None
- invalidates: None

## Success Criteria

- M902 writes a challenge benchmark design
- M902 names both challenge configs
- M902 defines policies, episodes, seeds, thresholds, and run dirs
- M902 defines failure routing
- M902 keeps benchmark execution, PPO, and promotion blocked

## Failure Criteria

- M902 runs the benchmark
- M902 admits PPO or promotion
- M902 omits one challenge config
- M902 omits pre-registered thresholds
- M902 treats challenge results as private holdout evidence

## Evidence Gates

- M902 must design benchmark for near-threshold robust challenge
- M902 must design benchmark for late high-energy robust challenge
- M902 must include M568, alpha_0_1 candidates, raw candidates, heuristic, and random
- M902 must pre-register success/termination non-regression and clearance thresholds
- M902 must keep PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run benchmark in M902
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not use challenge results as private holdout evidence

## Failure Taxonomy

- behavior_regression
- metric_artifact
- scenario_sampling_failure
- objective_overfit
- contract_violation
- lineage_invalid

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

Challenge-family raw scaling benchmark has not yet been designed
