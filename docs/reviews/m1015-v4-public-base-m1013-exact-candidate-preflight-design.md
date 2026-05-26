# m1015-v4-public-base-m1013-exact-candidate-preflight-design Research Review

## Summary

- Generated at UTC: 20260526T192011Z
- Type: gate
- Gate tier: process
- Promotion decision: m1013_exact_candidate_preflight_design_admit_m1016_implementation
- Decision reason: M1015 designs minimal M267/M264 preflight calibration for selected exact-but-branch-unsafe M1013 candidates before threshold relaxation or new update

## Hypothesis

A minimal M267/M264 preflight over selected exact-but-branch-unsafe M1013 candidates can determine whether M1011 trust thresholds are too conservative or necessary.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_001/raw_actor_mean_update.pt, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/checkpoints/lambda_0_03/raw_actor_mean_update.pt
- parent_dataset: docs/m1014-v4-public-base-margin-weighted-repair-failure-audit.md, runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/interpolation_metrics.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1014-v4-public-base-margin-weighted-repair-failure-audit.json
- parent_objective: design replay-calibrated M267/M264 preflight for exact-but-branch-unsafe M1013 candidates
- derived_from: m1014-v4-public-base-margin-weighted-repair-failure-audit
- blocked_by: M1014 requires replay calibration before threshold relaxation or new update
- supersedes: None
- invalidates: blind lambda sweep continuation after M1013

## Success Criteria

- design document exists
- selected candidates are specified
- preflight is limited to M267/M264 calibration
- PPO and promotion remain blocked

## Failure Criteria

- design routes directly to PPO
- design uses private holdout
- design treats preflight as promotion evidence
- design changes actor inputs

## Evidence Gates

- M1015 must not train
- M1015 must not run PPO
- M1015 must not promote
- M1015 must preserve P0 actor inputs
- M1015 must design only M267/M264 preflight calibration for selected M1013 exact candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not run full public replay stack before preflight calibration
- do not relax M1011 thresholds without replay evidence
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1015-v4-public-base-m1013-exact-candidate-preflight-design
- type: gate
- checkpoint: docs/m1015-v4-public-base-m1013-exact-candidate-preflight-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: m1013_exact_candidate_preflight_design_admit_m1016_implementation
- reason: M1015 designs minimal M267/M264 preflight calibration for selected exact-but-branch-unsafe M1013 candidates before threshold relaxation or new update

## Next Blocker

m1016-v4-public-base-m1013-exact-candidate-preflight
