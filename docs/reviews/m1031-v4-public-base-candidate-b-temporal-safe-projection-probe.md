# m1031-v4-public-base-candidate-b-temporal-safe-projection-probe Research Review

## Summary

- Generated at UTC: 20260526T231057Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: candidate_b_temporal_safe_projection_proof_washout
- Decision reason: M1031 finds 16 temporal/exact-safe projected candidates and 14 replay-eligible candidates; M267/M264 row15 can be retained but no candidate passes M183/M170 first replay so route to failure audit

## Hypothesis

A bounded interpolation from Candidate B to one M1029 repair candidate can satisfy M997 temporal exact retention while preserving enough M297/M270 repair signal to justify first replay gates.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1030-v4-public-base-candidate-b-temporal-retention-repair-design.md, runs/m1029_candidate_b_repair_temporal_exact_retention/exact_retention_summary.csv, runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/candidate_checkpoint.pt, runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/candidate_checkpoint.pt, runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/candidate_checkpoint.pt, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1030-v4-public-base-candidate-b-temporal-retention-repair-design.json
- parent_objective: run temporal-safe interpolation/projection over M1029 repair candidates before first replay
- derived_from: m1030-v4-public-base-candidate-b-temporal-retention-repair-design
- blocked_by: M1030 chooses temporal-safe projection before modifying exact_post_ppo_repair
- supersedes: None
- invalidates: running first replay on temporal-failing M1029 endpoints, relaxing M997 temporal gate thresholds

## Success Criteria

- projection metrics artifact exists
- candidate checkpoints for evaluated alphas exist
- at least one alpha passes M997 temporal exact and M297/M270 exact no-regression
- selected candidate passes M267/M264 first replay with row15 retained
- selected candidate passes M183/M170 first replay
- no PPO promotion private holdout or actor-input change occurs

## Failure Criteria

- no alpha passes M997 temporal exact
- temporal-safe alphas are base-equivalent only
- temporal-safe alphas fail M297/M270 exact no-regression
- selected candidate fails M267/M264 row15 or M183/M170 first replay
- actor inputs change

## Evidence Gates

- M1031 must run no PPO
- M1031 must not promote
- M1031 must not use private holdout
- M1031 must preserve P0 actor inputs
- M997 temporal exact retention must pass before M297/M270/replay acceptance
- M297/M270 exact no-regression must pass before replay
- M267/M264 row15 and M183/M170 first replay must pass before any full public gate route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not relax M997 thresholds
- do not run replay for temporal-failing alphas
- do not change actor inputs
- do not use private holdout
- do not promote any projection candidate

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1031-v4-public-base-candidate-b-temporal-safe-projection-probe
- type: driver_candidate
- checkpoint: runs/m1031_candidate_b_temporal_safe_projection_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_temporal_safe_projection_proof_washout
- reason: M1031 finds 16 temporal/exact-safe projected candidates and 14 replay-eligible candidates; M267/M264 row15 can be retained but no candidate passes M183/M170 first replay so route to failure audit

## Next Blocker

m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit
