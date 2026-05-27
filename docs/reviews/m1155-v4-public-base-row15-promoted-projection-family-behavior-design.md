# m1155-v4-public-base-row15-promoted-projection-family-behavior-design Research Review

## Summary

- Generated at UTC: 20260527T234710Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_projection_family_behavior_design_admit_diagnostic_run
- Decision reason: M1155 designs M1144 exact recheck plus expanded public diagnostic wrapper for alpha_0_05 while keeping promotion PPO and private holdout blocked

## Hypothesis

The M1154 alpha_0_05 first-replay candidate should next be tested on family-intersection replay and behavior diagnostics before any promotion, PPO, or private holdout.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run.md, runs/m1154_row15_promoted_unsafe_margin_projection_probe/summary.json, runs/m1154_row15_promoted_unsafe_margin_projection_probe/first_replay_summary.csv, runs/m1154_row15_promoted_unsafe_margin_projection_probe/failed_row_gate_rows.csv
- parent_config: experiments/manifests/m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run.json
- parent_objective: design family-intersection and behavior diagnostics for the M1154 selected alpha
- derived_from: m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run
- blocked_by: M1154 first replay candidate is not promotable without family and behavior diagnostics
- supersedes: None
- invalidates: promotion from M1154 first replay alone, PPO from alpha_0_05 before family/behavior diagnostics, private holdout before public proof diagnostics

## Success Criteria

- design artifact exists
- M1061 family-intersection replay scope is explicit
- behavior diagnostic scope is explicit
- failure routing is explicit
- promotion remains blocked
- no actor training, PPO, replay, behavior eval, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- family-intersection replay scope is ambiguous
- behavior diagnostic scope is ambiguous
- promotion route is accidentally admitted
- actor training, PPO, replay, behavior eval, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1155 must be design-only
- M1155 must not train actor weights
- M1155 must not run PPO
- M1155 must not run replay
- M1155 must not run behavior eval
- M1155 must not mine new rows
- M1155 must not promote
- M1155 must not use private holdout
- M1155 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run behavior eval
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip family-intersection replay
- do not treat M1154 first replay as promotion evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1155-v4-public-base-row15-promoted-projection-family-behavior-design
- type: gate
- checkpoint: docs/m1155-v4-public-base-row15-promoted-projection-family-behavior-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_projection_family_behavior_design_admit_diagnostic_run
- reason: M1155 designs M1144 exact recheck plus expanded public diagnostic wrapper for alpha_0_05 while keeping promotion PPO and private holdout blocked

## Next Blocker

m1156-v4-public-base-row15-promoted-projection-family-behavior-run
