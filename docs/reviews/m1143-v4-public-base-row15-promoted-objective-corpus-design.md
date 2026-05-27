# m1143-v4-public-base-row15-promoted-objective-corpus-design Research Review

## Summary

- Generated at UTC: 20260527T225312Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_objective_corpus_design_admit_objective_sanity_run
- Decision reason: M1143 designs row15_current objective sanity with 76 expected deduplicated rows minimum corpus rows 70 and no corpus build or training

## Hypothesis

A single-checkpoint boundary-outcome corpus/objective sanity run can be pre-registered for the M1142 row15_current materialized rows without violating hidden-state-space separation.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1142-v4-public-base-row15-promoted-target-materialization.md, runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv, runs/m1142_row15_promoted_target_materialization/row15_current_materialization_summary.json
- parent_config: experiments/manifests/m1142-v4-public-base-row15-promoted-target-materialization.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design boundary-outcome corpus and objective sanity run from row15_current materialized rows
- derived_from: m1142-v4-public-base-row15-promoted-target-materialization
- blocked_by: M1142 materialized row15_current rows are ready, but corpus/objective sanity must be pre-registered before writing NPZ
- supersedes: None
- invalidates: running objective sanity without pre-registered corpus thresholds, using any checkpoint other than row15_current for the first M1142 corpus, promoting from corpus/objective sanity

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

- M1143 must design only
- M1143 must not train actor weights
- M1143 must not run PPO
- M1143 must not run replay
- M1143 must not run corpus build or objective sanity
- M1143 must not mine rows
- M1143 must not promote
- M1143 must not use private holdout
- M1143 must preserve actor inputs

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
- do not conflate objective sanity with promotion

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1143-v4-public-base-row15-promoted-objective-corpus-design
- type: gate
- checkpoint: docs/m1143-v4-public-base-row15-promoted-objective-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_objective_corpus_design_admit_objective_sanity_run
- reason: M1143 designs row15_current objective sanity with 76 expected deduplicated rows minimum corpus rows 70 and no corpus build or training

## Next Blocker

m1144-v4-public-base-row15-promoted-objective-corpus-run
