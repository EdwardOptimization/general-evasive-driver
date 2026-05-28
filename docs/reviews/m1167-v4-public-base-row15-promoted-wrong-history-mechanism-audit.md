# m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit Research Review

## Summary

- Generated at UTC: 20260528T013634Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_wrong_history_mechanism_audit_route_to_target_margin_microgrid_design
- Decision reason: M1167 finds M1166 selected both old sensitive pairs but coarser target margins caused one false negative while the broader 240-pair sample still shows wrong-history scarcity

## Hypothesis

M1166 failed because relocation makes most matched wrong-history continuations safe; the audit can distinguish source-budget, target-policy, target-type, margin-window, and current-frame substitution causes using existing artifacts.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/summary.json, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/boundary_relocation_rows.csv, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/surface_summary.csv, runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/balanced_accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot.json
- parent_objective: audit why M1166 preserved a broad source budget but produced only one accepted wrong-history relocation row
- derived_from: m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot
- blocked_by: M1166 did not improve on M1161 and accepted only one wrong-history relocation row
- supersedes: None
- invalidates: larger same-shape relocation expansion without mechanism audit, conversion from the M1166 pilot surface, PPO from the M1166 pilot surface

## Success Criteria

- audit artifact exists
- M1161 and M1166 accepted-surface contrast is summarized
- wrong-history-safe versus wrong-history-failure rows are summarized by checkpoint, target, pair, margin, and action-distance evidence
- failure mechanism is classified
- next route is explicit
- no mining, outcome rerun, relocation replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- audit artifact is missing
- failure mechanism remains ambiguous
- next route remains ambiguous
- mining, outcome rerun, relocation replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1167 must audit existing M1161 and M1166 artifacts only
- M1167 must not rerun mining
- M1167 must not rerun outcome gate
- M1167 must not run relocation replay
- M1167 must not train actor weights
- M1167 must not run PPO
- M1167 must not promote
- M1167 must not use private holdout
- M1167 must preserve actor inputs
- M1167 must not convert the failed pilot surface

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun mining
- do not rerun outcome gate
- do not run relocation replay
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken thresholds
- do not convert the failed pilot surface

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit
- type: gate
- checkpoint: docs/m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_wrong_history_mechanism_audit_route_to_target_margin_microgrid_design
- reason: M1167 finds M1166 selected both old sensitive pairs but coarser target margins caused one false negative while the broader 240-pair sample still shows wrong-history scarcity

## Next Blocker

m1168-v4-public-base-row15-promoted-relocation-target-microgrid-design
