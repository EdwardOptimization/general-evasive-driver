# m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation Research Review

## Summary

- Generated at UTC: 20260526T063245Z
- Type: gate
- Gate tier: proof
- Promotion decision: direction_target_actor_fit_replay_gate_pass_route_to_promotion_generalization_design
- Decision reason: M966 selects M964 alpha 1.0 after 5/5 M267 preflight pass and passes all six public replay surfaces source-diverse diagnostics and behavior seeds without PPO or promotion

## Hypothesis

At least one M964 direction-target actor-fit candidate can pass no-training public replay/proof gates before PPO or promotion.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_5.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_2.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_1.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m965-v4-public-base-direction-target-actor-fit-replay-gate-design.md, runs/m964_v4_public_base_direction_target_actor_fit/summary.json, runs/m964_v4_public_base_direction_target_actor_fit/candidate_checkpoints.csv
- parent_config: experiments/manifests/m965-v4-public-base-direction-target-actor-fit-replay-gate-design.json
- parent_objective: implement no-training replay gate for M964 direction-target actor-fit candidates
- derived_from: m965-v4-public-base-direction-target-actor-fit-replay-gate-design, m964-v4-public-base-direction-target-actor-fit-objective-implementation
- blocked_by: M965 designs replay gate but M964 candidates have not been closed-loop replay gated
- supersedes: None
- invalidates: PPO or promotion before replay-gating M964 candidates

## Success Criteria

- summary artifact exists
- candidate preflight summary is written
- public replay gate summary is written
- behavior summary and comparison are written
- route decision is explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- implementation trains or updates model weights
- implementation changes actor inputs
- implementation omits M267/M264 preflight
- implementation omits public replay surfaces
- implementation omits behavior seeds
- implementation promotes a checkpoint

## Evidence Gates

- M966 must not train
- M966 must not run PPO
- M966 must not promote
- M966 must preserve the P0 actor-input contract
- M966 must run M267/M264 preflight over candidate alphas
- M966 must run six public replay surfaces for the selected candidate
- M966 must run behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not run PPO
- do not accept M964 target-fit metrics as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m966-v4-public-base-direction-target-actor-fit-replay-gate-implementation
- type: gate
- checkpoint: runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_actor_fit_replay_gate_pass_route_to_promotion_generalization_design
- reason: M966 selects M964 alpha 1.0 after 5/5 M267 preflight pass and passes all six public replay surfaces source-diverse diagnostics and behavior seeds without PPO or promotion

## Next Blocker

M964 direction-target actor-fit candidates have not been replay gated
