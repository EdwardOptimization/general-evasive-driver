# m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design Research Review

## Summary

- Generated at UTC: 20260527T233212Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_unsafe_margin_projection_design_admit_runner_implementation
- Decision reason: M1152 designs failed-row unsafe-margin projection with exact M1144 and M1149 first-replay gates but routes to runner implementation because the old M1123 projection probe is hardcoded for a single row15 cliff

## Hypothesis

A no-training interpolation along the M1147 exact-objective direction may admit a small nonzero alpha that improves exact M1144 objective while preserving wrong-history unsafe terminal margins on the M1149 failed rows.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt, runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- parent_dataset: docs/m1151-v4-public-base-row15-promoted-target-materialization-synthesis.md, runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv, runs/m1150_row15_promoted_first_replay_failure_audit/summary.json, runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
- parent_config: experiments/manifests/m1151-v4-public-base-row15-promoted-target-materialization-synthesis.json
- parent_objective: design a no-training unsafe-margin projection probe along the M1147 direction
- derived_from: m1151-v4-public-base-row15-promoted-target-materialization-synthesis
- blocked_by: M1151 closes direct actor-update continuation and opens row15_promoted_unsafe_margin_projection
- supersedes: None
- invalidates: generic actor update without wrong-history unsafe-margin screen, family-intersection replay before unsafe-margin projection, PPO from m1147_114602, promotion of m1147_114602

## Success Criteria

- design artifact exists
- candidate alpha grid is explicit
- unsafe-margin sign rule requires every M1149 failed wrong-history row to remain unsuccessful with terminal margin below zero
- normal-success retention requires every M1149 failed normal-history row to remain successful
- exact M1144 objective acceptance requires non-regression and prefers improvement
- M1153 implementation scope is limited to promoted unsafe-margin projection runner and focused tests only
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- alpha grid is ambiguous
- unsafe-margin rule is ambiguous
- exact objective rule is ambiguous
- implementation or run scope admits PPO, actor training, promotion, private holdout, or actor-input change

## Evidence Gates

- M1152 must be design-only
- M1152 must not train actor weights
- M1152 must not run PPO
- M1152 must not run replay
- M1152 must not mine new rows
- M1152 must not promote
- M1152 must not use private holdout
- M1152 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken M1149 first-replay thresholds
- do not accept an alpha that makes any M1149 failed wrong-history row safe

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design
- type: gate
- checkpoint: docs/m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_unsafe_margin_projection_design_admit_runner_implementation
- reason: M1152 designs failed-row unsafe-margin projection with exact M1144 and M1149 first-replay gates but routes to runner implementation because the old M1123 projection probe is hardcoded for a single row15 cliff

## Next Blocker

m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation
