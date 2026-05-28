# m1172-v4-public-base-wrong-history-action-divergence-artifact-audit Research Review

## Summary

- Generated at UTC: 20260528T015817Z
- Type: gate
- Gate tier: process
- Promotion decision: wrong_history_action_divergence_audit_route_to_candidate_export_design
- Decision reason: M1172 finds 151 combined action-divergent margin-sensitive rows across 8 physical pairs and 6 checkpoints but not enough diversity for direct proof conversion

## Hypothesis

Existing M1161 outcome artifacts may contain enough action-divergent and margin-sensitive wrong-history rows to design a stronger candidate replay without new mining.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1171-v4-public-base-stronger-wrong-history-construction-design.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_summary.csv
- parent_config: experiments/manifests/m1171-v4-public-base-stronger-wrong-history-construction-design.json
- parent_objective: audit existing M1161 outcome rows for action-divergent and terminal-margin-sensitive wrong histories
- derived_from: m1171-v4-public-base-stronger-wrong-history-construction-design
- blocked_by: M1171 designs an existing-artifact action-divergence audit before new mining or replay
- supersedes: None
- invalidates: new mining before checking existing action-divergent rows, replay before measuring intervention strength, PPO before a broader wrong-history proof surface exists

## Success Criteria

- audit artifact exists
- threshold counts for first_action_distance are reported
- threshold counts for action_trajectory_distance_mean are reported
- threshold counts for margin_gap are reported
- source diversity for promising rows is reported
- next route is explicit
- no mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- audit artifact is missing
- threshold availability remains ambiguous
- source diversity remains ambiguous
- next route remains ambiguous
- mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1172 must audit existing M1161 outcome artifacts only
- M1172 must not run mining
- M1172 must not run replay
- M1172 must not train actor weights
- M1172 must not run PPO
- M1172 must not promote
- M1172 must not use private holdout
- M1172 must preserve actor inputs
- M1172 must not convert rows

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
- do not convert rows
- do not claim success-drop proof from action-distance alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1172-v4-public-base-wrong-history-action-divergence-artifact-audit
- type: gate
- checkpoint: docs/m1172-v4-public-base-wrong-history-action-divergence-artifact-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_action_divergence_audit_route_to_candidate_export_design
- reason: M1172 finds 151 combined action-divergent margin-sensitive rows across 8 physical pairs and 6 checkpoints but not enough diversity for direct proof conversion

## Next Blocker

m1173-v4-public-base-action-divergent-candidate-export-design
