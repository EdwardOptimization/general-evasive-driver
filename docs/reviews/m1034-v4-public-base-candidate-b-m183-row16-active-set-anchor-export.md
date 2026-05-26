# m1034-v4-public-base-candidate-b-m183-row16-active-set-anchor-export Research Review

## Summary

- Generated at UTC: 20260526T233229Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: candidate_b_m183_row16_active_set_anchor_export_pass
- Decision reason: M1034 exports exact-loadable M183/M170 row16 normal trajectory anchor with 57 rows and no PPO repair promotion or actor-input change

## Hypothesis

M183/M170 row16 normal branch can be exported as an exact-loadable trajectory anchor from the Candidate B public-gate base without PPO, repair, promotion, private holdout, or actor-input change.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design.md, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m1031_candidate_b_temporal_safe_projection_probe/first_replay/m1031_raw_conflict_s40_a0_05/m183_m170/boundary_replay_rows.csv
- parent_config: experiments/manifests/m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design.json
- parent_objective: export Candidate B normal-trajectory anchor for M183/M170 row16 active-set retention
- derived_from: m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design
- blocked_by: M1033 requires M183/M170 row16 normal trajectory retention data before another repair/projection attempt
- supersedes: None
- invalidates: running repair before M183/M170 row16 retention data exists, using M183/M170 row16 as a narrative constraint without exact-loadable anchor data

## Success Criteria

- anchor npz exists
- anchor csv exists
- summary json exists
- anchor loads with load_trajectory_action_anchor
- anchor rows > 0
- source row is M183/M170 row16 normal branch
- no PPO repair promotion private holdout or actor-input change occurs

## Failure Criteria

- row16 cannot be reconstructed
- anchor is empty
- anchor cannot be loaded by existing objective tooling
- export uses wrong-history as the primary row16 branch
- export runs repair or PPO
- actor inputs change

## Evidence Gates

- M1034 must run no PPO
- M1034 must not run repair or promote
- M1034 must not use private holdout
- M1034 must preserve P0 actor inputs
- exported anchor must load through load_trajectory_action_anchor
- exported anchor must be normal branch for M183/M170 row16

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run exact repair
- do not promote
- do not change actor inputs
- do not export wrong-history row16 as the primary retention target
- do not relax M997 thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1034-v4-public-base-candidate-b-m183-row16-active-set-anchor-export
- type: infrastructure
- checkpoint: runs/m1034_candidate_b_m183_row16_active_set_anchor_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_m183_row16_active_set_anchor_export_pass
- reason: M1034 exports exact-loadable M183/M170 row16 normal trajectory anchor with 57 rows and no PPO repair promotion or actor-input change

## Next Blocker

m1035-v4-public-base-candidate-b-combined-active-set-repair-design
