# m1107-v4-public-base-materialized-objective-corpus-run Research Review

## Summary

- Generated at UTC: 20260527T200756Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: materialized_objective_corpus_pass_route_to_result_audit
- Decision reason: M1107 corpus passes with 68 rows 14 physical pairs 3 targets zero action reconstruction error and objective_pass true with seed_pass_count 3 and mean val pairwise accuracy 0.944444

## Hypothesis

The proof_current materialized rows can build a valid single-checkpoint boundary-outcome corpus and pass auxiliary objective sanity.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1106-v4-public-base-family-aggregate-conversion-synthesis.md, docs/m1105-v4-public-base-materialized-objective-corpus-design.md, runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv
- parent_config: experiments/manifests/m1106-v4-public-base-family-aggregate-conversion-synthesis.json, experiments/manifests/m1105-v4-public-base-materialized-objective-corpus-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: build proof_current boundary-outcome corpus and run auxiliary objective sanity
- derived_from: m1106-v4-public-base-family-aggregate-conversion-synthesis
- blocked_by: M1106 opens materialized_objective_corpus_sanity branch
- supersedes: None
- invalidates: actor update before objective sanity, promotion from objective sanity, running PPO from materialized rows

## Success Criteria

- corpus_summary.json exists
- objective_summary.json exists
- corpus_rows >= 60
- physical_pairs >= 10
- targets == 3
- success_drop_rows == corpus_rows
- action_reconstruction_error_max <= 0.005
- action_reconstruction_error_mean <= 0.001
- objective_pass is true
- seed_pass_count == 3
- no actor training, PPO, replay, mining, promotion, or private holdout occurs

## Failure Criteria

- corpus build fails
- corpus is sparse
- action reconstruction error exceeds threshold
- objective_pass is false
- actor training, PPO, replay, mining, promotion, or private holdout starts

## Evidence Gates

- M1107 may build corpus and run auxiliary objective sanity only
- M1107 must use proof_current only
- M1107 must not train actor weights
- M1107 must not run PPO
- M1107 must not run replay
- M1107 must not mine rows
- M1107 must not promote
- M1107 must not use private holdout
- M1107 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not interpret auxiliary objective pass as driver improvement

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1107-v4-public-base-materialized-objective-corpus-run
- type: objective_sanity
- checkpoint: runs/m1107_materialized_objective_corpus/objective_summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_objective_corpus_pass_route_to_result_audit
- reason: M1107 corpus passes with 68 rows 14 physical pairs 3 targets zero action reconstruction error and objective_pass true with seed_pass_count 3 and mean val pairwise accuracy 0.944444

## Next Blocker

m1108-v4-public-base-materialized-objective-result-audit
