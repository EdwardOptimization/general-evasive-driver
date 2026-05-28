# m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run Research Review

## Summary

- Generated at UTC: 20260528T002640Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_margin_slack_surface_refresh_reject_route_to_failure_audit
- Decision reason: M1161 source budget is ready but final accepted wrong-history surface has only 15 rows 2 physical pairs 1 target 1 margin bucket and max margin 0.002483 so it rejects before conversion or PPO

## Hypothesis

The alpha_0_05 public base has a source-diverse current-base wrong-history proof surface with at least three 0.005m normal-margin buckets and normal-margin max at least 0.01m.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design.md
- parent_config: experiments/manifests/m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design.json
- parent_objective: run current-base source-diverse surface refresh with explicit margin-slack thresholds
- derived_from: m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design
- blocked_by: M1160 designs the alpha_0_05 margin-slack surface refresh
- supersedes: None
- invalidates: PPO before current-base margin-slack surface refresh, private holdout before public surface refresh, objective conversion before surface quality is known

## Success Criteria

- matched current summary exists
- matched history outcome summary exists
- source-balanced relocation summary exists
- accepted_wrong_history_rows >= 100
- accepted_wrong_physical_pairs >= 12
- accepted_wrong_left_steps >= 6
- accepted_wrong_checkpoints >= 4
- accepted_wrong_targets >= 2
- accepted_wrong_normal_margin_buckets >= 3 at width 0.005
- accepted_wrong_normal_margin_max >= 0.01
- accepted_wrong_success_drop_fraction == 1.0
- max_rows_per_physical_pair_fraction <= 0.25
- control_accepted_wrong_rows == 0
- source_budget_ready == true
- no actor training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- any required summary artifact is missing
- source budget is not ready
- accepted surface is sparse
- margin buckets are sparse
- normal margin max is below 0.01
- duplicate dominance exceeds threshold
- control rows are accepted
- actor training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1161 may run the three-stage M1160 surface-refresh pipeline only
- M1161 must preserve pre-registered margin-slack and diversity thresholds
- M1161 must not train actor weights
- M1161 must not run PPO
- M1161 must not run replay beyond the matched-history outcome gate and relocation continuations
- M1161 must not promote
- M1161 must not use private holdout
- M1161 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken margin-slack thresholds after seeing results
- do not convert to an objective corpus inside this milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run
- type: gate
- checkpoint: runs/m1161_row15_promoted_margin_slack_surface_seed116100/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_margin_slack_surface_refresh_reject_route_to_failure_audit
- reason: M1161 source budget is ready but final accepted wrong-history surface has only 15 rows 2 physical pairs 1 target 1 margin bucket and max margin 0.002483 so it rejects before conversion or PPO

## Next Blocker

m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit
