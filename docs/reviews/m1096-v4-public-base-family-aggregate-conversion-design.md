# m1096-v4-public-base-family-aggregate-conversion-design Research Review

## Summary

- Generated at UTC: 20260527T191203Z
- Type: gate
- Gate tier: process
- Promotion decision: family_aggregate_conversion_design_admit_export_implementation
- Decision reason: M1096 designs an export-only family-aggregate raw-retained conversion contract that preserves source-policy metadata duplicate geometry and replay planning while blocking mixed-source objective NPZ

## Hypothesis

A family-aggregate raw-retained conversion contract can preserve the M1092 source-balanced surface while making source-policy metadata, duplicate geometry, replay sanity, and hidden-state handling explicit.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1095-v4-public-base-source-balanced-boundary-tooling-synthesis.md, docs/m1094-v4-public-base-source-balanced-compactability-audit.md, runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv, runs/m1094_source_balanced_compactability_audit/recommended_conversion_mode.json
- parent_config: experiments/manifests/m1095-v4-public-base-source-balanced-boundary-tooling-synthesis.json
- parent_objective: design a family-aggregate raw-retained conversion contract for the M1092 source-balanced surface
- derived_from: m1095-v4-public-base-source-balanced-boundary-tooling-synthesis
- blocked_by: M1094 recommends family-aggregate raw-retained conversion because per-checkpoint and compact-dedup aggregate conversion are sparse
- supersedes: None
- invalidates: using boundary_outcome_corpus_objective unchanged on M1092 as a per-checkpoint corpus, dropping duplicate raw-retained checkpoint rows without documenting the source-policy contract, running objective optimization before replay sanity

## Success Criteria

- conversion design artifact exists
- source-policy metadata contract is explicit
- raw-retained duplicate geometry semantics are explicit
- replay sanity requirements are explicit and precede objective optimization
- hidden-state/source-policy mixing is handled or explicitly avoided
- no training, PPO, replay, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- source-policy or duplicate-geometry contract is ambiguous
- replay sanity is missing
- hidden-state/source-policy mixing is ignored
- training, PPO, replay, mining, promotion, or private holdout starts

## Evidence Gates

- M1096 must design only
- M1096 must not train
- M1096 must not run PPO
- M1096 must not run replay
- M1096 must not mine rows
- M1096 must not promote
- M1096 must not use private holdout
- M1096 must preserve actor inputs
- M1096 must state how source-policy metadata and hidden-state spaces are handled

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken M1092 source-balanced thresholds
- do not silently mix source checkpoint hidden states without a contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1096-v4-public-base-family-aggregate-conversion-design
- type: gate
- checkpoint: docs/m1096-v4-public-base-family-aggregate-conversion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: family_aggregate_conversion_design_admit_export_implementation
- reason: M1096 designs an export-only family-aggregate raw-retained conversion contract that preserves source-policy metadata duplicate geometry and replay planning while blocking mixed-source objective NPZ

## Next Blocker

m1097-v4-public-base-family-aggregate-conversion-implementation
