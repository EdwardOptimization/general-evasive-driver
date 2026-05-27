# m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation Research Review

## Summary

- Generated at UTC: 20260527T233212Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1153 may only implement promoted unsafe-margin projection tooling and focused tests. It cannot train actor weights, run PPO, run full replay/projection evaluation, mine rows, promote, use private holdout, change actor inputs, or hardcode only the old M1120 row15 pair.

## Hypothesis

A promoted unsafe-margin projection runner can be implemented by reusing interpolation, exact objective evaluation, and boundary replay helpers while replacing the old hardcoded row15 surfaces with M1149 failed-row and first-replay inputs.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt, runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- parent_dataset: docs/m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design.md, runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv, runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
- parent_config: experiments/manifests/m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design.json
- parent_objective: implement the promoted unsafe-margin projection runner needed before the no-training projection run
- derived_from: m1152-v4-public-base-row15-promoted-unsafe-margin-projection-design
- blocked_by: M1152 finds the old M1123 projection tool is hardcoded for a single row15 cliff and cannot directly serve M1149 failed rows
- supersedes: None
- invalidates: using M1123 row15-only projection probe directly for M1149, projection run before promoted-runner implementation, PPO from m1147_114602, promotion of m1147_114602

## Success Criteria

- runner implementation exists
- focused tests cover alpha parsing, failed-row grouping, result classification, and guardrail metadata
- runner help/smoke works without executing full projection replay
- no actor training, PPO, full replay/projection evaluation, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- runner implementation is missing
- tests are missing or fail
- runner hardcodes only old M1120 row15 semantics
- runner scope accidentally runs projection replay, PPO, training, mining, promotion, or private holdout

## Evidence Gates

- M1153 may implement tooling and focused tests only
- M1153 must not train actor weights
- M1153 must not run PPO
- M1153 must not run full replay or projection evaluation
- M1153 must not mine new rows
- M1153 must not promote
- M1153 must not use private holdout
- M1153 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run full replay or projection evaluation
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not hardcode only the old M1120 row15 pair

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation
