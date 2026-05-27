# m1124-v4-public-base-row15-projection-family-replay-design Research Review

## Summary

- Generated at UTC: 20260527T213911Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_projection_family_replay_design_admit_m1125
- Decision reason: M1124 designs M1061 family-intersection public gate for alpha_0_15 with existing short61049 short61050 short61051 sources and unchanged replay thresholds before any full gate PPO or promotion

## Hypothesis

The alpha_0_15 first-replay candidate should next face the M1061 family-intersection public gate before any full public gate or promotion consideration.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1123-v4-public-base-row15-unsafe-margin-projection-probe.md, runs/m1123_row15_unsafe_margin_projection_probe/summary.json, runs/m1123_row15_unsafe_margin_projection_probe/first_replay_summary.csv, runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv, runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv, runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1123-v4-public-base-row15-unsafe-margin-projection-probe.json
- parent_objective: design family-intersection replay for the M1123 alpha_0_15 first-replay candidate
- derived_from: m1123-v4-public-base-row15-unsafe-margin-projection-probe
- blocked_by: M1123 passed only row15 unsafe-margin and target-base first replay
- supersedes: None
- invalidates: full public gate before family-intersection replay, fresh/OOD before family-intersection replay, PPO from alpha_0_15, promotion of alpha_0_15

## Success Criteria

- design artifact exists
- all three M1061 source policies and corpora are specified
- family replay thresholds match M1063/M1064
- next run scope blocks full public gate, fresh/OOD, behavior, PPO, promotion, and private holdout
- no actor training, PPO, replay, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- family replay command is ambiguous
- thresholds are weakened
- next route is ambiguous
- actor training, PPO, replay, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1124 must be design-only
- M1124 must not train actor weights
- M1124 must not run PPO
- M1124 must not run replay
- M1124 must not run full public gate
- M1124 must not run fresh/OOD or behavior gates
- M1124 must not promote
- M1124 must not use private holdout
- M1124 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run full public gate
- do not run fresh/OOD or behavior gates
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken family-intersection thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1124-v4-public-base-row15-projection-family-replay-design
- type: gate
- checkpoint: docs/m1124-v4-public-base-row15-projection-family-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_family_replay_design_admit_m1125
- reason: M1124 designs M1061 family-intersection public gate for alpha_0_15 with existing short61049 short61050 short61051 sources and unchanged replay thresholds before any full gate PPO or promotion

## Next Blocker

m1125-v4-public-base-row15-projection-family-replay
