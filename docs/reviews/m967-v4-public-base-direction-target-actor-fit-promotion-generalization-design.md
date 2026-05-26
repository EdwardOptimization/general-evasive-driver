# m967-v4-public-base-direction-target-actor-fit-promotion-generalization-design Research Review

## Summary

- Generated at UTC: 20260526T065349Z
- Type: gate
- Gate tier: promotion
- Promotion decision: direction_target_actor_fit_promotion_generalization_design_admit_m968
- Decision reason: M967 designs separate proof retention fresh randomized generalization behavior ablation and promotion decision tiers before alpha 1.0 promotion or PPO

## Hypothesis

The M966 replay-gate-passing alpha_1_0 candidate needs a separate promotion/generalization protocol before it can replace the current public-gate base or be used for PPO continuation.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation.md, runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/summary.json, runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/public_replay_gate_summary.csv, runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/behavior_comparison.csv
- parent_config: experiments/manifests/m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation.json
- parent_objective: design promotion and generalization protocol for the M966 replay-gate-passing direction-target actor-fit candidate
- derived_from: m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation, m964-v4-public-base-direction-target-actor-fit-objective-implementation
- blocked_by: M966 replay/proof gates passed, but no promotion/generalization protocol exists for alpha_1_0
- supersedes: None
- invalidates: promoting alpha_1_0 based only on public proof replay gates, running PPO continuation before generalization and promotion gates are designed

## Success Criteria

- design document exists
- proof gates are listed separately from generalization gates
- promotion criteria are explicit
- fresh randomized scenario distribution is scoped
- behavior retention and ablations are included
- holdout discipline is specified
- PPO and promotion remain blocked

## Failure Criteria

- design recommends promotion based only on M966 public replay pass
- design changes actor inputs
- design omits fresh randomized scenarios
- design omits behavior seeds or ablations
- design uses private holdout for iterative tuning
- design runs PPO

## Evidence Gates

- M967 must not train
- M967 must not run PPO
- M967 must not promote
- M967 must preserve the P0 actor-input contract
- M967 must separate proof, generalization, and promotion gates
- M967 must specify holdout discipline before using any private evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout evidence
- do not promote
- do not run PPO
- do not treat public proof-gate pass as sufficient promotion evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m967-v4-public-base-direction-target-actor-fit-promotion-generalization-design
- type: gate
- checkpoint: docs/m967-v4-public-base-direction-target-actor-fit-promotion-generalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_actor_fit_promotion_generalization_design_admit_m968
- reason: M967 designs separate proof retention fresh randomized generalization behavior ablation and promotion decision tiers before alpha 1.0 promotion or PPO

## Next Blocker

direction-target actor-fit alpha_1_0 has passed public replay gates but lacks a promotion/generalization protocol
