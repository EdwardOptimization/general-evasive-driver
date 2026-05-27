# m1135-v4-public-base-row15-promoted-replay-sanity-design Research Review

## Summary

- Generated at UTC: 20260527T222823Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_replay_sanity_design_admit_m1136_run
- Decision reason: M1135 designs source-aware replay sanity for M1134 aggregate rows with source-policy source-row gates cross-family report and duplicate geometry audit before objective conversion

## Hypothesis

M1134 source-preserving aggregate rows should be replay-sanity checked before any objective conversion or training.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv, runs/m1134_row15_promoted_family_aggregate_conversion/replay_plan.json, docs/m1134-v4-public-base-row15-promoted-family-aggregate-conversion.md
- parent_config: experiments/manifests/m1134-v4-public-base-row15-promoted-family-aggregate-conversion.json
- parent_objective: design source-aware replay sanity for the M1134 family aggregate rows before objective conversion
- derived_from: m1134-v4-public-base-row15-promoted-family-aggregate-conversion
- blocked_by: family aggregate rows have not been replay-sanity checked
- supersedes: None
- invalidates: objective conversion before source-aware replay sanity, training on aggregate rows before replay sanity

## Success Criteria

- design artifact exists
- replay command is explicit
- source-policy source-row gate is explicit
- cross-family report is explicit
- duplicate geometry audit is explicit
- no training, PPO, objective optimization, replay, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- replay source-policy map is ambiguous
- duplicate geometry handling is missing
- training, PPO, objective optimization, replay, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1135 must design replay sanity only
- M1135 must not train actor weights
- M1135 must not run PPO
- M1135 must not run objective optimization
- M1135 must not run replay
- M1135 must not promote
- M1135 must not use private holdout
- M1135 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run objective optimization
- do not run replay in the design milestone
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip duplicate-geometry failure reporting

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1135-v4-public-base-row15-promoted-replay-sanity-design
- type: gate
- checkpoint: docs/m1135-v4-public-base-row15-promoted-replay-sanity-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_replay_sanity_design_admit_m1136_run
- reason: M1135 designs source-aware replay sanity for M1134 aggregate rows with source-policy source-row gates cross-family report and duplicate geometry audit before objective conversion

## Next Blocker

m1136-v4-public-base-row15-promoted-replay-sanity
