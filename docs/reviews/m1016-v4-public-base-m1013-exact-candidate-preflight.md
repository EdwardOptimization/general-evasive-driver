# m1016-v4-public-base-m1013-exact-candidate-preflight Research Review

## Summary

- Generated at UTC: 20260526T192650Z
- Type: gate
- Gate tier: proof
- Promotion decision: m1013_exact_candidate_preflight_metric_ordering_artifact_route_to_signed_branch_metric_audit
- Decision reason: M1016 finds Candidate B lambda0.03 alpha0.5 passes M267/M264 while lower branch-loss Candidate A fails rows 6 and 15 so unsigned branch L2 ordering is a metric artifact

## Hypothesis

Selected M1013 exact-but-branch-unsafe candidates will reveal whether M1011 branch trust thresholds are conservative or necessary by their M267/M264 preflight result.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_001/raw_actor_mean_update.pt, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_03/raw_actor_mean_update.pt
- parent_dataset: docs/m1015-v4-public-base-m1013-exact-candidate-preflight-design.md, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/interpolation_metrics.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1015-v4-public-base-m1013-exact-candidate-preflight-design.json
- parent_objective: materialize selected M1013 exact candidates and run M267/M264 preflight calibration
- derived_from: m1015-v4-public-base-m1013-exact-candidate-preflight-design
- blocked_by: M1015 requires public proof preflight calibration before threshold relaxation
- supersedes: None
- invalidates: threshold relaxation without M267/M264 evidence

## Success Criteria

- summary.json exists
- selected candidate checkpoints are materialized
- non-actor checksum matches M974 base for all candidates
- M267/M264 preflight runs for selected candidates
- PPO and promotion remain blocked

## Failure Criteria

- candidate materialization changes non-actor parameters
- PPO starts
- promotion occurs
- private holdout is used

## Evidence Gates

- M1016 must not train
- M1016 must not run PPO
- M1016 must not promote
- M1016 must preserve P0 actor inputs
- M1016 must run only M267/M264 preflight calibration

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run full public replay stack
- do not use private holdout
- do not treat preflight pass as promotion
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1016-v4-public-base-m1013-exact-candidate-preflight
- type: gate
- checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: m1013_exact_candidate_preflight_metric_ordering_artifact_route_to_signed_branch_metric_audit
- reason: M1016 finds Candidate B lambda0.03 alpha0.5 passes M267/M264 while lower branch-loss Candidate A fails rows 6 and 15 so unsigned branch L2 ordering is a metric artifact

## Next Blocker

m1017-v4-public-base-signed-branch-metric-audit
