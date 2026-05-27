# m1050-v4-public-base-guarded-ppo-short-escalation-repeat Research Review

## Summary

- Generated at UTC: 20260527T035318Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: guarded_ppo_short_escalation_repeat_pass_route_to_synthesis
- Decision reason: M1050 runs two fresh 4096-step guarded PPO repeats and both raw checkpoints pass exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Hypothesis

Two fresh 4096-step guarded PPO proposals from the M1045 public-gate base can complete with finite metrics and preserve exact, proof, source-diverse, fresh/OOD, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- parent_dataset: docs/m1049-v4-public-base-guarded-ppo-short-escalation-smoke.md, runs/m1049_guarded_ppo_short_escalation_seed61049/summary.json
- parent_config: configs/ppo_m1049_guarded_short_escalation_seed61049.json, experiments/manifests/m1049-v4-public-base-guarded-ppo-short-escalation-smoke.json
- parent_objective: repeat the 4096-step guarded PPO short-escalation recipe on two fresh seeds without promotion
- derived_from: m1049-v4-public-base-guarded-ppo-short-escalation-smoke
- blocked_by: M1049 is one 4096-step seed and does not prove short-escalation repeatability
- supersedes: None
- invalidates: promoting or lengthening PPO from a single 4096-step seed

## Success Criteria

- configs for seeds 61050 and 61051 exist
- both PPO runs complete and write checkpoints
- both training metric sets are finite
- both actor input contracts are unchanged
- both exact and combined active-set gates pass
- both six-surface public replay gate stacks pass
- both source-diverse diagnostics pass
- both fresh public and moderate-OOD gates pass
- both behavior ablation gates pass
- both row15 and row16 rollback checks pass
- aggregate repeat summary is written
- no promotion or private holdout occurs

## Failure Criteria

- a PPO run crashes or checkpoint is missing
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

- M1050 must run exactly two fresh 4096-step guarded PPO repeats
- M1050 must not promote
- M1050 must not use private holdout
- M1050 must preserve the P0 actor-input contract for both raw checkpoints
- M1050 must gate each raw checkpoint against exact M997/M297/M270 and combined active-set checks
- M1050 must gate each raw checkpoint against six public proof replay surfaces
- M1050 must gate source-diverse diagnostics, fresh public seeds, moderate-OOD seed, and behavior ablations
- M1050 must fail on any M267/M264 row15 wrong-history success or M183/M170 row16 normal-history failure

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1050
- do not skip exact or combined active-set checks
- do not skip proof replay gates
- do not accept aggregate eval if row15 or row16 proof washes out
- do not change loss coefficients while testing repeatability

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1050-v4-public-base-guarded-ppo-short-escalation-repeat
- type: driver_candidate
- checkpoint: runs/m1050_guarded_ppo_short_escalation_repeat_summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_ppo_short_escalation_repeat_pass_route_to_synthesis
- reason: M1050 runs two fresh 4096-step guarded PPO repeats and both raw checkpoints pass exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Next Blocker

m1051-v4-public-base-guarded-ppo-short-escalation-synthesis
