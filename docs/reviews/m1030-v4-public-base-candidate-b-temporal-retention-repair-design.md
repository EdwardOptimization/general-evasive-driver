# m1030-v4-public-base-candidate-b-temporal-retention-repair-design Research Review

## Summary

- Generated at UTC: 20260526T222359Z
- Type: gate
- Gate tier: process
- Promotion decision: candidate_b_temporal_retention_design_admit_projection_probe
- Decision reason: M1030 chooses temporal-safe interpolation/projection over M1029 repair candidates before objective integration or first replay

## Hypothesis

M997 temporal retention should be made a first-class repair/projection constraint so exact M297/M270 row15 repair candidates cannot drift temporally before first replay.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe.md, runs/m1029_candidate_b_repair_temporal_exact_retention/exact_retention_summary.csv, runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/summary.json, runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/summary.json, runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/summary.json, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe.json
- parent_objective: design temporal-retention-aware exact repair after M1029 exact repair candidates fail M997 temporal exact gate
- derived_from: m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe
- blocked_by: M1029 exact repair candidates pass M297/M270 but all fail M997 temporal exact due action drift above 0.015
- supersedes: None
- invalidates: running first replay for M1029 temporal-regressing candidates, longer PPO before temporal-retention-aware repair design

## Success Criteria

- design artifact exists
- temporal-retention objective or projection option is specified
- gate order remains exact temporal before first replay
- next implementation scope is bounded
- no training repair PPO promotion or private holdout occurs

## Failure Criteria

- design relaxes M997 thresholds
- design omits M267/M264 row15 retention
- design runs repair or PPO
- design changes actor inputs
- design promotes a candidate

## Evidence Gates

- M1030 must design only and not train
- M1030 must not run PPO or repair
- M1030 must not promote
- M1030 must not use private holdout
- M1030 must preserve P0 actor inputs
- M1030 must make M997 temporal retention first-class before first replay

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not relax M997 temporal action-drift thresholds
- do not run first replay for temporal-regressing candidates
- do not run longer PPO
- do not change actor inputs
- do not promote repair candidates from the design milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1030-v4-public-base-candidate-b-temporal-retention-repair-design
- type: gate
- checkpoint: docs/m1030-v4-public-base-candidate-b-temporal-retention-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_temporal_retention_design_admit_projection_probe
- reason: M1030 chooses temporal-safe interpolation/projection over M1029 repair candidates before objective integration or first replay

## Next Blocker

m1031-v4-public-base-candidate-b-temporal-safe-projection-probe
