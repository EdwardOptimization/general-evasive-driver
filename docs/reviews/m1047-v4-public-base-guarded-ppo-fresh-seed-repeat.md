# m1047-v4-public-base-guarded-ppo-fresh-seed-repeat Research Review

## Summary

- Generated at UTC: 20260527T030024Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: guarded_ppo_fresh_seed_repeat_pass_route_to_short_escalation_design
- Decision reason: M1047 runs two fresh 1024-step guarded PPO repeats from the current public-gate base and both pass exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Hypothesis

Two fresh 1024-step guarded PPO proposals from the M1045 public-gate base can run and pass exact, proof, source-diverse, fresh generalization, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- parent_dataset: docs/m1046-v4-public-base-guarded-ppo-post-promotion-synthesis.md, runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/summary.json
- parent_config: configs/ppo_m1044_combined_active_set_guarded_smoke.json, experiments/manifests/m1046-v4-public-base-guarded-ppo-post-promotion-synthesis.json
- parent_objective: run fresh-seed guarded PPO smoke repeats from the M1045 public-gate base and gate each without promotion
- derived_from: m1046-v4-public-base-guarded-ppo-post-promotion-synthesis
- blocked_by: M1044 is a single PPO seed and does not prove seed-stable PPO continuation
- supersedes: None
- invalidates: escalating to longer PPO before fresh-seed smoke repeat

## Success Criteria

- seed 61045 raw PPO run completes
- seed 61046 raw PPO run completes
- both summary artifacts exist
- both exact contract summaries are written
- both proof replay summaries are written
- both behavior comparisons are written
- aggregate repeat summary is written
- route decision is explicit
- no promotion or private holdout occurs

## Failure Criteria

- a PPO run crashes
- actor inputs change
- exact or combined active-set gates are skipped
- proof replay gates are skipped
- fresh generalization or behavior gates are skipped
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1047 must run only two smoke-scale PPO repeats
- M1047 must not promote
- M1047 must not use private holdout
- M1047 must preserve the P0 actor-input contract
- M1047 must gate each raw PPO checkpoint against exact and combined active-set checks
- M1047 must gate each raw PPO checkpoint against proof replay, source-diverse diagnostics, fresh generalization, and behavior ablations

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1047
- do not skip combined active-set checks
- do not skip proof replay gates
- do not accept aggregate eval if row15 or row16 proof washes out

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1047-v4-public-base-guarded-ppo-fresh-seed-repeat
- type: driver_candidate
- checkpoint: runs/m1047_guarded_ppo_fresh_seed_repeat_summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_ppo_fresh_seed_repeat_pass_route_to_short_escalation_design
- reason: M1047 runs two fresh 1024-step guarded PPO repeats from the current public-gate base and both pass exact proof source-diverse fresh public moderate-OOD and behavior gates without promotion

## Next Blocker

m1048-v4-public-base-guarded-ppo-short-escalation-design
