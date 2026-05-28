# m1172-v4-public-base-wrong-history-action-divergence-artifact-audit Research Review

## Summary

- Generated at UTC: 20260528T015341Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1172 may only audit existing M1161 outcome artifacts. It cannot run mining, run replay, train actor weights, run PPO, promote, use private holdout, change actor inputs, convert rows, or claim proof from action-distance alone.

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

- No scoreboard row recorded.

## Next Blocker

m1172-v4-public-base-wrong-history-action-divergence-artifact-audit
