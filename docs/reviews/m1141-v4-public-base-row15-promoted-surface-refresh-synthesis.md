# m1141-v4-public-base-row15-promoted-surface-refresh-synthesis Research Review

## Summary

- Generated at UTC: 20260527T224754Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_surface_refresh_synthesis_open_target_materialization
- Decision reason: M1141 closes row15_promoted_base_surface_refresh and opens row15_promoted_target_materialization with 148 all-policy rows ready for current-base materialization

## Hypothesis

M1131-M1140 have produced a broad enough row15-current promoted-base proof surface to close the refresh branch and open target materialization implementation.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1131-v4-public-base-row15-promoted-surface-refresh-design.md, docs/m1132-v4-public-base-row15-promoted-surface-refresh.md, docs/m1133-v4-public-base-row15-promoted-compact-conversion-design.md, docs/m1134-v4-public-base-row15-promoted-family-aggregate-conversion.md, docs/m1135-v4-public-base-row15-promoted-replay-sanity-design.md, docs/m1136-v4-public-base-row15-promoted-replay-sanity.md, docs/m1137-v4-public-base-row15-promoted-cross-family-replay-audit.md, docs/m1138-v4-public-base-row15-promoted-intersection-selector-design.md, docs/m1139-v4-public-base-row15-promoted-intersection-selector.md, docs/m1140-v4-public-base-row15-promoted-target-materialization-design.md
- parent_config: experiments/manifests/m1140-v4-public-base-row15-promoted-target-materialization-design.json
- parent_objective: synthesize row15 promoted-base surface refresh branch before target materialization implementation
- derived_from: m1131-v4-public-base-row15-promoted-surface-refresh-design, m1140-v4-public-base-row15-promoted-target-materialization-design
- blocked_by: workflow synthesis cadence reached after M1140
- supersedes: None
- invalidates: continuing row15_promoted_base_surface_refresh without synthesis, running target materialization implementation before branch-level evidence review, overclaiming M1131-M1140 as PPO readiness or driver improvement evidence

## Success Criteria

- synthesis artifact exists
- evidence summary is explicit
- supported claims are explicit
- falsified or unsupported claims are explicit
- failure taxonomy summary is explicit
- public-gate overfit risk is explicit
- next branch decision is explicit
- no actor training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- synthesis artifact is missing
- supported and unsupported claims are conflated
- next branch decision is ambiguous
- actor training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1141 must synthesize M1131-M1140 branch evidence
- M1141 must not train actor weights
- M1141 must not run PPO
- M1141 must not run replay
- M1141 must not run objective optimization
- M1141 must not mine rows
- M1141 must not promote
- M1141 must not use private holdout
- M1141 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not start target materialization implementation before synthesis

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1141-v4-public-base-row15-promoted-surface-refresh-synthesis
- type: gate
- checkpoint: docs/m1141-v4-public-base-row15-promoted-surface-refresh-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_surface_refresh_synthesis_open_target_materialization
- reason: M1141 closes row15_promoted_base_surface_refresh and opens row15_promoted_target_materialization with 148 all-policy rows ready for current-base materialization

## Next Blocker

m1142-v4-public-base-row15-promoted-target-materialization
