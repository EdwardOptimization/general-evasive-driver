# m1044-v4-public-base-combined-active-set-guarded-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260527T022514Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: combined_active_set_guarded_ppo_raw_candidate_route_to_promotion_audit
- Decision reason: M1044 runs one 1024-step guarded PPO proposal and raw checkpoint passes exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Hypothesis

A 1024-step guarded PPO proposal from the combined active-set public-gate base can run and be evaluated against exact, proof, source-diverse, fresh generalization, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- parent_dataset: docs/m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
- parent_config: configs/ppo_m1026_candidate_b_guarded_smoke.json, experiments/manifests/m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design.json
- parent_objective: run one smoke-scale guarded PPO proposal from the combined active-set public-gate base and gate it without promotion
- derived_from: m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design
- blocked_by: M1044 was pending before the smoke PPO proposal and gates were run
- supersedes: None
- invalidates: longer PPO from the combined active-set base before auditing M1044, promoting the M1044 raw PPO checkpoint from aggregate generalization or behavior retention alone

## Success Criteria

- config artifact exists
- raw PPO run completes
- summary artifact exists
- exact contract summary is written
- proof replay summary is written
- fresh randomized eval summary is written
- OOD eval summary is written
- behavior summary and comparison are written
- route decision is explicit
- no promotion or private holdout occurs

## Failure Criteria

- PPO run crashes
- actor inputs change
- exact or combined active-set gates are skipped
- proof replay gates are skipped
- fresh generalization or behavior gates are skipped
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1044 must run only smoke-scale PPO
- M1044 must not promote
- M1044 must not use private holdout
- M1044 must preserve the P0 actor-input contract
- M1044 must gate raw PPO against M997, M297/M270, and combined active-set exact checks
- M1044 must gate raw PPO against proof replay, source-diverse diagnostics, fresh generalization, and behavior ablations

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1044
- do not skip combined active-set checks
- do not skip proof replay gates
- do not accept aggregate eval if row15 or row16 proof washes out

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1044-v4-public-base-combined-active-set-guarded-ppo-smoke
- type: driver_candidate
- checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_active_set_guarded_ppo_raw_candidate_route_to_promotion_audit
- reason: M1044 runs one 1024-step guarded PPO proposal and raw checkpoint passes exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Next Blocker

m1045-v4-public-base-combined-active-set-guarded-ppo-promotion-audit
