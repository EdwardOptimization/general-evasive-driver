# m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design Research Review

## Summary

- Generated at UTC: 20260526T100152Z
- Type: gate
- Gate tier: process
- Promotion decision: exact_post_ppo_repair_projection_design_admit_m974
- Decision reason: M973 designs no-PPO exact full-corpus repair/projection for M972 raw before any longer PPO promotion or private holdout

## Hypothesis

M972's useful but proof-washing PPO proposal should be handled as a noisy proposal followed by exact lexicographic repair/projection, not by longer PPO or larger scalar auxiliary pressure.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
- parent_dataset: runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/summary.json, runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/proof_replay_summary.csv, runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/proof_gates/m267_m264_replay/boundary_replay_rows.csv, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
- parent_config: experiments/manifests/m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation.json, configs/ppo_m972_post_promotion_guarded_smoke.json
- parent_objective: M972 smoke PPO proposal preserved fresh/behavior gates but washed out M267/M264 wrong-history proof rows 6 and 15
- derived_from: m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation, m971-v4-public-base-post-promotion-guarded-ppo-readiness-design
- blocked_by: M972 raw PPO checkpoint fails M267/M264 success-drop retention 17 -> 15
- supersedes: None
- invalidates: longer PPO from M972 raw checkpoint before exact repair/projection design, promotion of runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt

## Success Criteria

- M973 writes an exact repair/projection design document
- the design names base checkpoint, raw PPO checkpoint, exact proof objectives, and acceptance order
- the design keeps PPO, promotion, private holdout, and actor-input changes blocked
- the design routes implementation to a separate milestone

## Failure Criteria

- design recommends longer PPO before exact repair
- design accepts M972 raw despite M267/M264 proof washout
- design changes the actor input contract
- design uses private holdout
- design lacks a proof-first acceptance order

## Evidence Gates

- M973 must not run PPO
- M973 must not promote a checkpoint
- M973 must not use private holdout
- M973 must preserve the P0 actor-input contract
- M973 must design exact full-corpus proof objectives before replay promotion
- M973 must route any implementation to a separate pre-registered milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lengthen PPO
- do not increase scalar PPO auxiliary coefficients as the main fix
- do not accept aggregate fresh or behavior pass as sufficient
- do not change actor inputs
- do not tune on private holdout
- do not promote M972 raw

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design
- type: gate
- checkpoint: docs/m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: exact_post_ppo_repair_projection_design_admit_m974
- reason: M973 designs no-PPO exact full-corpus repair/projection for M972 raw before any longer PPO promotion or private holdout

## Next Blocker

m974-v4-public-base-post-promotion-exact-repair-projection-probe
