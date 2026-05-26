# m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe Research Review

## Summary

- Generated at UTC: 20260526T220955Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: candidate_b_post_ppo_exact_repair_temporal_regression
- Decision reason: M1029 gets 3/3 M297/M270 exact candidates but 0/3 pass M997 temporal exact action-drift gate so first replay and promotion remain blocked

## Hypothesis

The M1026 raw PPO proposal contains useful movement that can be repaired by exact full-corpus projection with M393 current-family conflict residual while retaining temporal exact and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design.md, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design.json
- parent_objective: run no-PPO exact post-PPO repair/projection candidates for M1026 raw PPO and gate exact plus first replay before any full public gate
- derived_from: m1028-v4-public-base-candidate-b-post-ppo-exact-repair-design
- blocked_by: M1028 design admitted exact repair/projection probe with M393 row15 conflict residual
- supersedes: None
- invalidates: longer PPO before exact repair probe, promotion of M1026 raw PPO checkpoint

## Success Criteria

- three repair candidate summaries exist or explicit failures are logged
- at least one candidate passes exact M297 and M270 no-regression versus Candidate B
- selected candidate passes M997 temporal exact retention
- selected candidate passes M267/M264 first replay with row15 retained
- selected candidate passes M183/M170 first replay
- no PPO promotion private holdout or actor-input change occurs

## Failure Criteria

- all candidates regress exact M297 or M270
- exact-passing candidate regresses M997 temporal retention
- exact-passing candidate fails M267/M264 row15 or surface retention
- exact-passing candidate fails M183/M170 first replay
- repair only reproduces base-equivalent movement with no useful raw proposal retention
- actor input contract changes

## Evidence Gates

- M1029 must run no PPO
- M1029 must not promote
- M1029 must not use private holdout
- M1029 must preserve P0 actor inputs
- exact M297 and M270 must pass before first replay
- M997 temporal exact retention must pass before first replay acceptance
- M267/M264 row15 must remain wrong-history failing
- M267/M264 and M183/M170 first replay must pass before routing to full public gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run full public gates for exact-regressing candidates
- do not promote any repair candidate
- do not use private holdout
- do not change actor inputs
- do not relax M267/M264 row15 or success-drop retention

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe
- type: driver_candidate
- checkpoint: runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_post_ppo_exact_repair_temporal_regression
- reason: M1029 gets 3/3 M297/M270 exact candidates but 0/3 pass M997 temporal exact action-drift gate so first replay and promotion remain blocked

## Next Blocker

m1030-v4-public-base-candidate-b-temporal-retention-repair-design
