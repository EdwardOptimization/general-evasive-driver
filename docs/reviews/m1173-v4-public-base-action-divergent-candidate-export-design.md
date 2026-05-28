# m1173-v4-public-base-action-divergent-candidate-export-design Research Review

## Summary

- Generated at UTC: 20260528T020327Z
- Type: gate
- Gate tier: proof
- Promotion decision: action_divergent_candidate_export_design_admit_export_tooling
- Decision reason: M1173 designs a score-balanced export pool with 343 rows across 17 physical pairs 3 targets and 6 checkpoints before bounded replay

## Hypothesis

A filtered or score-balanced candidate export from existing M1161 outcome rows can preserve action divergence while avoiding the two-pair collapse that blocked same-shape relocation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1172-v4-public-base-wrong-history-action-divergence-artifact-audit.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
- parent_config: experiments/manifests/m1172-v4-public-base-wrong-history-action-divergence-artifact-audit.json
- parent_objective: design an action-divergent candidate export before bounded relocation replay
- derived_from: m1172-v4-public-base-wrong-history-action-divergence-artifact-audit
- blocked_by: M1172 finds candidate signal exists but direct proof corpus diversity is limited
- supersedes: None
- invalidates: direct conversion from M1172 threshold rows, bounded replay from the unfiltered M1161 outcome CSV, new mining before trying an existing-artifact action-divergent export

## Success Criteria

- design artifact exists
- candidate export rule is explicit
- minimum rows, physical pairs, targets, checkpoints, and max pair fraction are explicit
- next export or tooling step is explicit
- no replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- candidate export rule is equivalent to unfiltered M1161
- candidate export rule collapses to old two-pair surface
- next route is ambiguous
- replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1173 is design-only
- M1173 must not run replay
- M1173 must not run mining
- M1173 must not train actor weights
- M1173 must not run PPO
- M1173 must not promote
- M1173 must not use private holdout
- M1173 must preserve actor inputs
- M1173 must not convert rows

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run replay
- do not run mining
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert rows
- do not claim proof from candidate export alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1173-v4-public-base-action-divergent-candidate-export-design
- type: gate
- checkpoint: docs/m1173-v4-public-base-action-divergent-candidate-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_candidate_export_design_admit_export_tooling
- reason: M1173 designs a score-balanced export pool with 343 rows across 17 physical pairs 3 targets and 6 checkpoints before bounded replay

## Next Blocker

m1174-v4-public-base-action-divergent-candidate-export-tooling
