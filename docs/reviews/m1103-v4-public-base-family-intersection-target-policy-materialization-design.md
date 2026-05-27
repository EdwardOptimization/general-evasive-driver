# m1103-v4-public-base-family-intersection-target-policy-materialization-design Research Review

## Summary

- Generated at UTC: 20260527T194948Z
- Type: gate
- Gate tier: process
- Promotion decision: target_policy_materialization_design_admit_implementation
- Decision reason: M1103 designs proof_current target-policy materialization so objective rows use proof_current replay margins/actions and preserve source metadata without writing objective NPZ

## Hypothesis

A target-policy materialization contract can convert M1102 all-policy intersection rows into objective-ready rows for one checkpoint without mixing source hidden-state spaces.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1102-v4-public-base-family-aggregate-intersection-selector-implementation.md, runs/m1102_family_aggregate_intersection_selector/family_intersection_rows.csv, runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv
- parent_config: experiments/manifests/m1102-v4-public-base-family-aggregate-intersection-selector-implementation.json
- parent_objective: design target-policy materialization before objective-ready boundary row conversion
- derived_from: m1102-v4-public-base-family-aggregate-intersection-selector-implementation
- blocked_by: M1102 selector passes, but direct objective conversion would mix source-policy labels and source-row metrics
- supersedes: None
- invalidates: feeding family_intersection_rows.csv directly into boundary_outcome_corpus_objective, mixing hidden-state spaces across source policies in one objective corpus, using source-row margins when optimizing a different target policy

## Success Criteria

- design artifact exists
- target policy selection is explicit
- source metadata preservation is explicit
- target-policy objective field mapping is explicit
- required boundary-outcome columns are covered
- fail-closed behavior is explicit
- no training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- target policy selection is ambiguous
- source and target fields are conflated
- required boundary-outcome columns are not mapped
- training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1103 must design only
- M1103 must not train
- M1103 must not run PPO
- M1103 must not run replay
- M1103 must not run objective optimization
- M1103 must not mine rows
- M1103 must not promote
- M1103 must not use private holdout
- M1103 must preserve actor inputs
- materialization design must preserve source metadata while emitting single-target-policy objective-ready rows

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not write a mixed-source objective NPZ
- do not reuse source-row margins for a different target policy

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1103-v4-public-base-family-intersection-target-policy-materialization-design
- type: gate
- checkpoint: docs/m1103-v4-public-base-family-intersection-target-policy-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: target_policy_materialization_design_admit_implementation
- reason: M1103 designs proof_current target-policy materialization so objective rows use proof_current replay margins/actions and preserve source metadata without writing objective NPZ

## Next Blocker

m1104-v4-public-base-family-intersection-target-policy-materialization-implementation
