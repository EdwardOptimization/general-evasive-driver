# m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation Research Review

## Summary

- Generated at UTC: 20260526T100152Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: post_promotion_guarded_ppo_proof_washout
- Decision reason: M972 PPO completes and fresh/behavior gates pass but M267/M264 proof success-drop regresses 17 to 15 so no promotion

## Hypothesis

A 1024-step guarded PPO proposal from alpha_1_0 can run and be evaluated against proof, fresh generalization, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m971-v4-public-base-post-promotion-guarded-ppo-readiness-design.md, configs/ppo_m972_post_promotion_guarded_smoke.json, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
- parent_config: experiments/manifests/m971-v4-public-base-post-promotion-guarded-ppo-readiness-design.json, configs/ppo_m972_post_promotion_guarded_smoke.json
- parent_objective: run one smoke-scale guarded PPO proposal from alpha_1_0 and gate it without promotion
- derived_from: m971-v4-public-base-post-promotion-guarded-ppo-readiness-design, m970-v4-public-base-direction-target-actor-fit-post-promotion-synthesis
- blocked_by: M971 designs readiness but the smoke PPO proposal has not been run
- supersedes: None
- invalidates: longer PPO from alpha_1_0 before smoke proposal proof/generalization result

## Success Criteria

- raw PPO run completes
- summary artifact exists
- proof replay summary is written
- fresh randomized eval summary is written
- OOD eval summary is written
- behavior summary and comparison are written
- route decision is explicit
- no promotion or private holdout occurs

## Failure Criteria

- PPO run crashes
- actor inputs change
- proof replay gates are skipped
- fresh generalization or behavior gates are skipped
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M972 must run only smoke-scale PPO
- M972 must not promote
- M972 must not use private holdout
- M972 must preserve the P0 actor-input contract
- M972 must gate raw PPO against alpha_1_0 proof replay stack
- M972 must gate raw PPO against fresh generalization and behavior ablations

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M972
- do not skip proof replay gates
- do not accept aggregate eval if wrong-history proof washes out

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation
- type: driver_candidate
- checkpoint: runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_promotion_guarded_ppo_proof_washout
- reason: M972 PPO completes and fresh/behavior gates pass but M267/M264 proof success-drop regresses 17 to 15 so no promotion

## Next Blocker

m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design
