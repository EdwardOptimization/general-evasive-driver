# m899-v4-pair-delta-raw-scaling-fresh-generalization-design Research Review

## Summary

- Generated at UTC: 20260525T202300Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: not_applicable
- Decision reason: M899 may only design the fresh/generalization benchmark. It must not run benchmark, train, run PPO, or promote.

## Hypothesis

Raw candidates passed public proof gates, so the next safe step is a no-training fresh/generalization benchmark design that tests usefulness without PPO or promotion.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m898-v4-pair-delta-raw-scaling-gate-audit.md, runs/m897_raw_controlled_scaling_full_replay_gate/summary.json, runs/m897_raw_controlled_scaling_behavior_seed9505/policy_summary.csv, runs/m897_raw_controlled_scaling_behavior_seed9506/policy_summary.csv
- parent_config: experiments/manifests/m898-v4-pair-delta-raw-scaling-gate-audit.json
- parent_objective: design no-training fresh/generalization benchmark for raw scaling candidates before integration, PPO, or promotion
- derived_from: m898-v4-pair-delta-raw-scaling-gate-audit
- blocked_by: raw candidates have public proof-gate retention but no fresh/generalization evidence
- supersedes: None
- invalidates: None

## Success Criteria

- M899 writes a benchmark design document
- M899 names all candidate and baseline policies
- M899 defines seeds, episodes, config, and run dirs for later execution
- M899 defines acceptance and failure criteria
- M899 keeps benchmark execution, PPO, and promotion blocked

## Failure Criteria

- M899 runs the benchmark
- M899 admits PPO or promotion
- M899 omits alpha_0_1 or raw comparison
- M899 lacks pre-registered thresholds
- M899 treats fresh benchmark as private holdout

## Evidence Gates

- M899 must design fresh/generalization benchmark only
- M899 must include M568, alpha_0_1, raw candidates, heuristic, and random
- M899 must pre-register success and termination non-regression
- M899 must pre-register clearance effect-size threshold
- M899 must keep PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run benchmark in M899
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat public proof gates as generalization
- do not use private holdout results for tuning

## Failure Taxonomy

- objective_overfit
- behavior_regression
- metric_artifact
- scenario_sampling_failure
- contract_violation
- lineage_invalid

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

Raw scaling candidates have not yet been evaluated on a pre-registered fresh/generalization benchmark
