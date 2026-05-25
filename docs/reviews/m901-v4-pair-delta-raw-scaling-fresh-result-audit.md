# m901-v4-pair-delta-raw-scaling-fresh-result-audit Research Review

## Summary

- Generated at UTC: 20260525T203542Z
- Type: gate
- Gate tier: process
- Promotion decision: margin_only_fresh_pass_route_to_challenge_generalization_design
- Decision reason: M901 audits M900 as margin-only fresh pass and routes to challenge-family generalization design before integration PPO or promotion

## Hypothesis

M900 provides a useful margin-only fresh signal, but it must be audited before deciding between another fresh scenario family, public-base integration design, or richer corpus construction.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark.md, runs/m900_raw_scaling_fresh_generalization_seed9705/policy_summary.csv, runs/m900_raw_scaling_fresh_generalization_seed9706/policy_summary.csv, runs/m900_raw_scaling_fresh_generalization_seed_delta/policy_delta_summary.csv
- parent_config: experiments/manifests/m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark.json
- parent_objective: audit M900 fresh benchmark result and choose next route after margin-only pass
- derived_from: m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark
- blocked_by: M900 passed fresh clearance threshold but produced no success flips, so routing is not yet decided
- supersedes: None
- invalidates: None

## Success Criteria

- M901 records M900 aggregate and seed-delta results
- M901 separates margin lift from success improvement
- M901 chooses the next route
- M901 keeps PPO and promotion blocked

## Failure Criteria

- M901 promotes raw candidates
- M901 admits PPO
- M901 claims success improvement
- M901 omits public diagnostic limitations
- M901 skips routing

## Evidence Gates

- M901 must separate margin-only pass from success improvement
- M901 must decide next route without PPO or promotion
- M901 must record public diagnostic limitation
- M901 must keep actor contract unchanged
- M901 must not claim private holdout evidence

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not claim success improvement from clearance-only movement
- do not route directly to private holdout tuning

## Failure Taxonomy

- metric_artifact
- objective_overfit
- behavior_regression
- scenario_sampling_failure
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m901-v4-pair-delta-raw-scaling-fresh-result-audit
- type: gate
- checkpoint: docs/m901-v4-pair-delta-raw-scaling-fresh-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_only_fresh_pass_route_to_challenge_generalization_design
- reason: M901 audits M900 as margin-only fresh pass and routes to challenge-family generalization design before integration PPO or promotion

## Next Blocker

M900 fresh margin-only pass has not yet been audited for next-route selection
