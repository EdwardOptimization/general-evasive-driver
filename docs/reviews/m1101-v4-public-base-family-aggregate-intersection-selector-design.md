# m1101-v4-public-base-family-aggregate-intersection-selector-design Research Review

## Summary

- Generated at UTC: 20260527T194012Z
- Type: gate
- Gate tier: process
- Promotion decision: family_aggregate_intersection_selector_design_admit_implementation
- Decision reason: M1101 designs a deterministic selector that keeps only all-policy normal-success wrong-history-failure rows and requires at least 80 rows 10 physical pairs 4 source labels 3 targets and 8 left steps before objective conversion

## Hypothesis

A deterministic family-intersection selector can safely convert M1099 cross-family replay results into a replay-calibrated row set before objective optimization.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1100-v4-public-base-family-aggregate-cross-family-replay-audit.md, runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv, runs/m1099_family_aggregate_replay_sanity/cross_family_policy_summary.csv, runs/m1099_family_aggregate_replay_sanity/failed_duplicate_geometry_groups.csv
- parent_config: experiments/manifests/m1100-v4-public-base-family-aggregate-cross-family-replay-audit.json
- parent_objective: design a deterministic family-intersection selector over M1099 replay-calibrated rows
- derived_from: m1100-v4-public-base-family-aggregate-cross-family-replay-audit
- blocked_by: M1100 chooses family-intersection replay-calibrated rows as the next safe route before objective optimization
- supersedes: None
- invalidates: direct mixed-source objective optimization over all 146 family rows, source-specific objective corpora as the first route while a broad all-policy intersection exists, target-base hidden-state row rebuild before selector sparsity is proven

## Success Criteria

- design artifact exists
- selector keep/drop rule is explicit
- input and output artifacts are explicit
- minimum diversity thresholds are explicit
- source and duplicate metadata preservation is explicit
- fail-closed behavior is explicit
- no training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- selector keep/drop rule is ambiguous
- diversity thresholds are missing
- source or duplicate metadata can be lost
- training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1101 must design only
- M1101 must not train
- M1101 must not run PPO
- M1101 must not run replay
- M1101 must not run objective optimization
- M1101 must not mine rows
- M1101 must not promote
- M1101 must not use private holdout
- M1101 must preserve actor inputs
- selector design must fail closed if all-policy intersection diversity becomes sparse

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
- do not include rows that fail all-policy normal-success and wrong-history-failure replay
- do not discard source or duplicate geometry metadata

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1101-v4-public-base-family-aggregate-intersection-selector-design
- type: gate
- checkpoint: docs/m1101-v4-public-base-family-aggregate-intersection-selector-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: family_aggregate_intersection_selector_design_admit_implementation
- reason: M1101 designs a deterministic selector that keeps only all-policy normal-success wrong-history-failure rows and requires at least 80 rows 10 physical pairs 4 source labels 3 targets and 8 left steps before objective conversion

## Next Blocker

m1102-v4-public-base-family-aggregate-intersection-selector-implementation
