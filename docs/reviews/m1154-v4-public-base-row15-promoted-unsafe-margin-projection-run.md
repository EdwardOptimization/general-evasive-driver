# m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run Research Review

## Summary

- Generated at UTC: 20260527T233917Z
- Type: gate
- Gate tier: proof
- Promotion decision: repair
- Decision reason: M1154 may only run no-training projection and selected-alpha M1149 first replay. It cannot train actor weights, run PPO, mine rows, promote, use private holdout, change actor inputs, run M1061 family-intersection replay, run fresh/OOD, run behavior gates, weaken thresholds, or try another alpha after selected first-replay failure inside this milestone.

## Hypothesis

A small nonzero alpha along the M1147 direction can retain the exact M1144 objective improvement while restoring M1149 failed-row wrong-history unsafe margins and selected-alpha first replay.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt, runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- parent_dataset: docs/m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation.md, runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv, runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
- parent_config: experiments/manifests/m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation.json
- parent_objective: run the no-training promoted unsafe-margin projection probe
- derived_from: m1153-v4-public-base-row15-promoted-unsafe-margin-projection-runner-implementation
- blocked_by: M1153 implements the promoted unsafe-margin projection runner
- supersedes: None
- invalidates: actor training before projection run, PPO from m1147_114602, family-intersection replay before projection result, promotion of any M1154 candidate

## Success Criteria

- summary artifact exists
- candidate alpha grid is evaluated
- failed-row unsafe-margin screen is evaluated for all 76 M1149 failed rows
- selected alpha is nonzero if a candidate exists
- selected alpha improves exact M1144 objective
- selected alpha preserves M1149 failed-row unsafe margins
- selected alpha either passes M1149 first replay or routes to failure audit
- no actor training, PPO, mining, promotion, private holdout, actor-input change, family-intersection replay, fresh/OOD, or behavior gate occurs

## Failure Criteria

- summary artifact is missing
- candidate alpha grid is not evaluated
- failed-row unsafe-margin screen is missing
- result class is ambiguous
- actor training, PPO, mining, promotion, private holdout, actor-input change, family-intersection replay, fresh/OOD, or behavior gate starts

## Evidence Gates

- M1154 may run only no-training interpolation/projection and selected-alpha M1149 first replay
- M1154 must not train actor weights
- M1154 must not run PPO
- M1154 must not mine new rows
- M1154 must not promote
- M1154 must not use private holdout
- M1154 must preserve actor inputs
- M1154 must not run M1061 family-intersection replay or behavior gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not run M1061 family-intersection replay
- do not run fresh/OOD or behavior gates
- do not weaken M1149 first-replay thresholds
- do not try another alpha after selected-alpha first replay failure inside this milestone

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run
