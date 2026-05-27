# m1138-v4-public-base-row15-promoted-intersection-selector-design Research Review

## Summary

- Generated at UTC: 20260527T223632Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_intersection_selector_design_admit_m1139_run
- Decision reason: M1138 designs deterministic family-intersection selector over M1136 replay rows with thresholds rows>=100 physical_pairs>=12 source_labels>=4 targets>=2 left_steps>=6

## Hypothesis

The M1137 all-policy intersection is broad enough to admit a deterministic family-intersection selector before objective conversion.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv, docs/m1137-v4-public-base-row15-promoted-cross-family-replay-audit.md
- parent_config: experiments/manifests/m1137-v4-public-base-row15-promoted-cross-family-replay-audit.json
- parent_objective: design deterministic family-intersection selector for all-policy-pass rows
- derived_from: m1137-v4-public-base-row15-promoted-cross-family-replay-audit
- blocked_by: all-policy intersection rows have not been selected into a compact replay-calibrated surface
- supersedes: None
- invalidates: direct mixed-family objective optimization, source-specific objective fallback before trying broad all-policy intersection

## Success Criteria

- design artifact exists
- selector command is explicit
- thresholds are explicit
- source metadata preservation is explicit
- no selector run, replay, objective optimization, training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- selector thresholds are missing
- direct mixed-family objective is admitted
- selector, replay, objective optimization, training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1138 must design intersection selector only
- M1138 must not run selector
- M1138 must not train actor weights
- M1138 must not run PPO
- M1138 must not run replay
- M1138 must not run objective optimization
- M1138 must not promote
- M1138 must not use private holdout
- M1138 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not run selector in the design milestone
- do not promote
- do not use private holdout
- do not change actor inputs
- do not admit direct mixed-family objective optimization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1138-v4-public-base-row15-promoted-intersection-selector-design
- type: gate
- checkpoint: docs/m1138-v4-public-base-row15-promoted-intersection-selector-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_intersection_selector_design_admit_m1139_run
- reason: M1138 designs deterministic family-intersection selector over M1136 replay rows with thresholds rows>=100 physical_pairs>=12 source_labels>=4 targets>=2 left_steps>=6

## Next Blocker

m1139-v4-public-base-row15-promoted-intersection-selector
