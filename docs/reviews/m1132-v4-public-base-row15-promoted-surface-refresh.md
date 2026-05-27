# m1132-v4-public-base-row15-promoted-surface-refresh Research Review

## Summary

- Generated at UTC: 20260527T222030Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_surface_refresh_pass_route_to_compact_conversion_design
- Decision reason: M1132 passes source-balanced promoted-base refresh with 172 accepted wrong rows 15 physical pairs 6 left steps 5 checkpoints 3 targets 3 margin buckets success-drop fraction 1.0 and zero control rows

## Hypothesis

The promoted alpha_0_15 public-gate base still exposes a fresh source-diverse wrong-history boundary surface suitable for later conversion.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1131-v4-public-base-row15-promoted-surface-refresh-design.md
- parent_config: experiments/manifests/m1131-v4-public-base-row15-promoted-surface-refresh-design.json
- parent_objective: run the source-diverse current-base surface refresh designed in M1131
- derived_from: m1131-v4-public-base-row15-promoted-surface-refresh-design
- blocked_by: fresh source-diverse current-base proof surface has not been mined under alpha_0_15
- supersedes: None
- invalidates: starting PPO from alpha_0_15 before promoted-base surface refresh, converting old active rows as if they were fresh current-base rows

## Success Criteria

- matched-current ambiguity artifact exists
- matched-history outcome artifact exists
- source-balanced relocation summary exists
- accepted_wrong_history_rows >= 100
- accepted_wrong_physical_pairs >= 12
- accepted_wrong_left_steps >= 6
- accepted_wrong_checkpoints >= 4
- accepted_wrong_targets >= 2
- accepted_wrong_normal_margin_buckets >= 2
- accepted_wrong_success_drop_fraction == 1.0
- max_rows_per_physical_pair_fraction <= 0.25
- control_accepted_wrong_rows == 0
- no actor training, PPO, objective optimization, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- source budget is insufficient
- accepted row count or diversity thresholds fail
- wrong-history success-drop fraction is below 1.0
- control rows are accepted
- actor training, PPO, objective optimization, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1132 may run the M1131 pre-registered matched-current, outcome, and source-balanced relocation commands
- M1132 must not train actor weights
- M1132 must not run PPO
- M1132 must not run objective optimization
- M1132 must not promote
- M1132 must not use private holdout
- M1132 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run objective optimization
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken thresholds after seeing the result
- do not skip source-balanced relocation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1132-v4-public-base-row15-promoted-surface-refresh
- type: gate
- checkpoint: runs/m1132_row15_promoted_source_balanced_surface_seed113200/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_surface_refresh_pass_route_to_compact_conversion_design
- reason: M1132 passes source-balanced promoted-base refresh with 172 accepted wrong rows 15 physical pairs 6 left steps 5 checkpoints 3 targets 3 margin buckets success-drop fraction 1.0 and zero control rows

## Next Blocker

m1133-v4-public-base-row15-promoted-compact-conversion-design
