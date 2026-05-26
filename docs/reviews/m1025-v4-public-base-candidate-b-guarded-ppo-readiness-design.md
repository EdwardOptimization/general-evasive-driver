# m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design Research Review

## Summary

- Generated at UTC: 20260526T205331Z
- Type: gate
- Gate tier: process
- Promotion decision: candidate_b_guarded_ppo_readiness_design_admit_m1026_smoke
- Decision reason: M1025 designs exactly one 1024-step guarded PPO smoke proposal from Candidate B with exact temporal proof replay fresh public OOD behavior and rollback gates

## Hypothesis

A smoke-scale guarded PPO proposal from Candidate B should only be attempted after explicit exact/proof/generalization/behavior rollback criteria are designed.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1024-v4-public-base-candidate-b-post-promotion-synthesis.md, runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/summary.json
- parent_config: experiments/manifests/m1024-v4-public-base-candidate-b-post-promotion-synthesis.json
- parent_objective: design guarded PPO readiness protocol from the Candidate B public-gate base
- derived_from: m1024-v4-public-base-candidate-b-post-promotion-synthesis
- blocked_by: Candidate B is promoted but PPO continuation has no guarded readiness protocol yet
- supersedes: None
- invalidates: running PPO directly from Candidate B without readiness design

## Success Criteria

- design artifact exists
- base checkpoint and PPO proposal scope are explicit
- proof, generalization, behavior, and rollback gates are specified
- PPO, promotion, and private holdout remain blocked

## Failure Criteria

- design runs PPO
- design omits replay proof retention
- design omits fresh public checks
- design omits rollback criteria
- design allows promotion from smoke PPO

## Evidence Gates

- M1025 must design PPO readiness only
- M1025 must not run PPO
- M1025 must not promote
- M1025 must not use private holdout
- M1025 must preserve P0 actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in the design milestone
- do not change actor inputs
- do not use private holdout
- do not promote from smoke PPO
- do not omit rollback criteria

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design
- type: gate
- checkpoint: docs/m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_guarded_ppo_readiness_design_admit_m1026_smoke
- reason: M1025 designs exactly one 1024-step guarded PPO smoke proposal from Candidate B with exact temporal proof replay fresh public OOD behavior and rollback gates

## Next Blocker

m1026-v4-public-base-candidate-b-guarded-ppo-smoke
