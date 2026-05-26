# m969-v4-public-base-direction-target-actor-fit-promotion-audit Research Review

## Summary

- Generated at UTC: 20260526T080926Z
- Type: gate
- Gate tier: promotion
- Promotion decision: direction_target_actor_fit_promote_public_gate_base
- Decision reason: M969 promotes M964 alpha 1.0 as the new public-gate base after M966 replay and M968 proof generalization behavior gates pass

## Hypothesis

M964 alpha_1_0 has enough public proof, fresh generalization, and behavior evidence to be promoted as the new public-gate base, while still blocking PPO and private-holdout claims.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m968-v4-public-base-direction-target-actor-fit-promotion-generalization-gate-implementation.md, runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/summary.json, docs/m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation.md, runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/summary.json
- parent_config: experiments/manifests/m968-v4-public-base-direction-target-actor-fit-promotion-generalization-gate-implementation.json
- parent_objective: audit whether M964 alpha_1_0 should become the new public-gate base
- derived_from: m968-v4-public-base-direction-target-actor-fit-promotion-generalization-gate-implementation, m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation
- blocked_by: M968 classifies alpha_1_0 as a promotion-gate candidate, but promotion has not been audited or recorded
- supersedes: None
- invalidates: using alpha_1_0 as public-gate base without a promotion audit

## Success Criteria

- audit document exists
- M966 result is cited
- M968 result is cited
- promotion or rejection decision is explicit
- public-gate base status is updated if promoted
- PPO and private holdout remain blocked

## Failure Criteria

- audit promotes without checking M966 and M968 evidence
- audit changes actor inputs
- audit runs PPO
- audit uses private holdout evidence
- audit omits promotion caveats

## Evidence Gates

- M969 must not train
- M969 must not run PPO
- M969 must not use private holdout
- M969 must preserve the P0 actor-input contract
- M969 must verify M966 public replay pass
- M969 must verify M968 proof/generalization/behavior pass
- M969 must explicitly decide whether to update the public-gate base

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not run PPO
- do not promote without recording lineage and non-promotion caveats

## Failure Taxonomy

- none

## Scoreboard

- milestone: m969-v4-public-base-direction-target-actor-fit-promotion-audit
- type: gate
- checkpoint: docs/m969-v4-public-base-direction-target-actor-fit-promotion-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_actor_fit_promote_public_gate_base
- reason: M969 promotes M964 alpha 1.0 as the new public-gate base after M966 replay and M968 proof generalization behavior gates pass

## Next Blocker

M968 classifies alpha_1_0 as a promotion candidate but promotion has not been audited
