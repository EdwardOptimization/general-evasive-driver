# m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit Research Review

## Summary

- Generated at UTC: 20260528T003148Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_margin_slack_failure_audit_route_to_relocation_expansion_design
- Decision reason: M1162 audits M1161 as relocation active-set collapse and wrong-history scarcity rather than source-budget failure and routes to bounded relocation expansion design

## Hypothesis

M1161 failed after relocation rather than source-budget generation; the likely blocker is a relocation/active-set surface collapse into duplicate low-slack wrong-history rows.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run.md, runs/m1161_row15_promoted_margin_slack_matched_current_seed116100/summary.json, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/summary.json, runs/m1161_row15_promoted_margin_slack_surface_seed116100/summary.json, runs/m1161_row15_promoted_margin_slack_surface_seed116100/robustness_gates.csv, runs/m1161_row15_promoted_margin_slack_surface_seed116100/surface_summary.csv, runs/m1161_row15_promoted_margin_slack_surface_seed116100/balanced_accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run.json
- parent_objective: audit why the alpha_0_05 current-base margin-slack surface refresh failed after strong source-budget and candidate-selection stages
- derived_from: m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run
- blocked_by: M1161 rejects the surface because accepted wrong-history rows are sparse, duplicate-dominated, and low-slack
- supersedes: None
- invalidates: objective conversion from M1161, PPO from the failed surface, threshold weakening without failure audit

## Success Criteria

- audit artifact exists
- source-budget and candidate-selection evidence is summarized
- accepted-surface failure is summarized by rows, pairs, targets, buckets, and slack
- failure mechanism is classified
- next route is explicit
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- audit artifact is missing
- source-budget versus relocation-collapse classification remains ambiguous
- next route is ambiguous
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1162 must audit existing M1161 artifacts only
- M1162 must not run mining
- M1162 must not run replay
- M1162 must not train actor weights
- M1162 must not run PPO
- M1162 must not promote
- M1162 must not use private holdout
- M1162 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run mining
- do not run replay
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken thresholds before classifying the failure
- do not convert the failed M1161 surface

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit
- type: gate
- checkpoint: docs/m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_margin_slack_failure_audit_route_to_relocation_expansion_design
- reason: M1162 audits M1161 as relocation active-set collapse and wrong-history scarcity rather than source-budget failure and routes to bounded relocation expansion design

## Next Blocker

m1163-v4-public-base-row15-promoted-relocation-expansion-design
