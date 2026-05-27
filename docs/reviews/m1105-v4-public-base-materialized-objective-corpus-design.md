# m1105-v4-public-base-materialized-objective-corpus-design Research Review

## Summary

- Generated at UTC: 20260527T200118Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_objective_corpus_design_route_to_branch_synthesis
- Decision reason: M1105 designs proof_current materialized corpus/objective sanity with expected 68 deduplicated rows corpus threshold 60 and explicit action-reconstruction/objective gates then routes to synthesis before objective run

## Hypothesis

A single-checkpoint boundary-outcome corpus/objective sanity run can be pre-registered for the M1104 proof_current materialized rows without violating hidden-state-space separation.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1104-v4-public-base-family-intersection-target-policy-materialization-implementation.md, runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv, runs/m1104_target_policy_materialization/proof_current_materialization_summary.json
- parent_config: experiments/manifests/m1104-v4-public-base-family-intersection-target-policy-materialization-implementation.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design boundary-outcome corpus and objective sanity run from proof_current materialized rows
- derived_from: m1104-v4-public-base-family-intersection-target-policy-materialization-implementation
- blocked_by: M1104 materialized proof_current rows are ready, but corpus/objective sanity must be pre-registered before writing NPZ
- supersedes: None
- invalidates: running objective sanity without pre-registered corpus thresholds, using any checkpoint other than proof_current for the first materialized corpus, promoting from corpus/objective sanity

## Success Criteria

- design artifact exists
- corpus command is explicit
- objective sanity command is explicit
- corpus thresholds are explicit
- action reconstruction and objective pass/fail interpretation are explicit
- no actor training, PPO, replay, corpus build, objective sanity, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- corpus command is ambiguous
- objective sanity pass/fail thresholds are missing
- objective sanity is conflated with promotion
- actor training, PPO, replay, corpus build, objective sanity, mining, promotion, or private holdout starts

## Evidence Gates

- M1105 must design only
- M1105 must not train actor weights
- M1105 must not run PPO
- M1105 must not run replay
- M1105 must not run corpus build or objective sanity
- M1105 must not mine rows
- M1105 must not promote
- M1105 must not use private holdout
- M1105 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run corpus build
- do not run objective sanity
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1105-v4-public-base-materialized-objective-corpus-design
- type: gate
- checkpoint: docs/m1105-v4-public-base-materialized-objective-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_objective_corpus_design_route_to_branch_synthesis
- reason: M1105 designs proof_current materialized corpus/objective sanity with expected 68 deduplicated rows corpus threshold 60 and explicit action-reconstruction/objective gates then routes to synthesis before objective run

## Next Blocker

m1106-v4-public-base-family-aggregate-conversion-synthesis
