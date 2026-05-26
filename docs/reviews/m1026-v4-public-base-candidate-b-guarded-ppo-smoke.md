# m1026-v4-public-base-candidate-b-guarded-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260526T213251Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: candidate_b_guarded_ppo_proof_washout
- Decision reason: M1026 trains 1024 PPO steps and exact fresh OOD behavior pass but M267/M264 proof replay drops from 17 to 16 so no promotion or longer PPO

## Hypothesis

A 1024-step guarded PPO proposal from Candidate B can run and be evaluated against exact, proof, fresh generalization, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
- parent_config: configs/ppo_m972_post_promotion_guarded_smoke.json, experiments/manifests/m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design.json
- parent_objective: run one smoke-scale guarded PPO proposal from Candidate B and gate it without promotion
- derived_from: m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design
- blocked_by: M1026 was pending before the smoke PPO proposal and gates were run
- supersedes: None
- invalidates: longer PPO from Candidate B before auditing M1026 proof washout, promoting the M1026 raw PPO checkpoint from aggregate generalization or behavior retention alone

## Success Criteria

- raw PPO run completes
- summary artifact exists
- exact retention summary is written
- proof replay summary is written
- fresh randomized eval summary is written
- OOD eval summary is written
- behavior summary and comparison are written
- route decision is explicit
- no promotion or private holdout occurs

## Failure Criteria

- PPO run crashes
- actor inputs change
- exact retention gates are skipped
- proof replay gates are skipped
- fresh generalization or behavior gates are skipped
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1026 must run only smoke-scale PPO
- M1026 must not promote
- M1026 must not use private holdout
- M1026 must preserve the P0 actor-input contract
- M1026 must gate raw PPO against exact temporal retention
- M1026 must gate raw PPO against proof replay, fresh generalization, and behavior ablations

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1026
- do not skip proof replay gates
- do not accept aggregate eval if wrong-history proof washes out

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1026-v4-public-base-candidate-b-guarded-ppo-smoke
- type: driver_candidate
- checkpoint: runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_guarded_ppo_proof_washout
- reason: M1026 trains 1024 PPO steps and exact fresh OOD behavior pass but M267/M264 proof replay drops from 17 to 16 so no promotion or longer PPO

## Next Blocker

m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit
