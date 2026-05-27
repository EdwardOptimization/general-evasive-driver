# m1049-v4-public-base-guarded-ppo-short-escalation-smoke Research Review

## Summary

- Generated at UTC: 20260527T033210Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: guarded_ppo_short_escalation_raw_candidate_route_to_fresh_seed_repeat
- Decision reason: M1049 runs one 4096-step guarded PPO proposal and raw checkpoint passes exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Hypothesis

One 4096-step guarded PPO proposal from the M1045 public-gate base can complete with finite metrics and preserve exact, proof, source-diverse, fresh/OOD, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- parent_dataset: docs/m1047-v4-public-base-guarded-ppo-fresh-seed-repeat.md, runs/m1047_guarded_ppo_fresh_seed_repeat_summary.json, docs/m1048-v4-public-base-guarded-ppo-short-escalation-design.md
- parent_config: configs/ppo_m1047_guarded_repeat_seed61045.json, experiments/manifests/m1048-v4-public-base-guarded-ppo-short-escalation-design.json
- parent_objective: run one 4096-step guarded PPO proposal from the M1045 public-gate base and gate it without promotion
- derived_from: m1048-v4-public-base-guarded-ppo-short-escalation-design
- blocked_by: M1047 passed 1024-step fresh-seed repeats but does not prove a longer PPO proposal remains proof-safe
- supersedes: None
- invalidates: claiming short PPO escalation stability without a 4096-step gated proposal

## Success Criteria

- config configs/ppo_m1049_guarded_short_escalation_seed61049.json exists
- PPO run completes and writes runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
- training metrics are finite
- actor inputs are unchanged
- exact and combined active-set gates pass
- all six public replay surfaces pass
- source-diverse diagnostics pass
- fresh public and moderate-OOD gates pass
- behavior ablation gates pass
- row15 and row16 rollback checks pass
- no promotion or private holdout occurs

## Failure Criteria

- PPO run crashes or checkpoint is missing
- training metrics are non-finite
- actor inputs change
- exact or combined active-set gate fails
- a public replay surface fails
- row15 wrong-history branch becomes successful
- row16 normal-history branch becomes unsuccessful
- fresh/OOD or behavior gate regresses
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1049 must run exactly one 4096-step guarded PPO proposal
- M1049 must not promote
- M1049 must not use private holdout
- M1049 must preserve the P0 actor-input contract
- M1049 must gate the raw PPO checkpoint against exact M997/M297/M270 and combined active-set checks
- M1049 must gate the raw PPO checkpoint against six public proof replay surfaces
- M1049 must gate source-diverse diagnostics, fresh public seeds, moderate-OOD seed, and behavior ablations
- M1049 must fail on M267/M264 row15 wrong-history success or M183/M170 row16 normal-history failure

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1049
- do not skip exact or combined active-set checks
- do not skip proof replay gates
- do not accept aggregate eval if row15 or row16 proof washes out
- do not change loss coefficients while testing the short escalation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1049-v4-public-base-guarded-ppo-short-escalation-smoke
- type: driver_candidate
- checkpoint: runs/m1049_guarded_ppo_short_escalation_seed61049/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_ppo_short_escalation_raw_candidate_route_to_fresh_seed_repeat
- reason: M1049 runs one 4096-step guarded PPO proposal and raw checkpoint passes exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Next Blocker

m1050-v4-public-base-guarded-ppo-short-escalation-repeat
