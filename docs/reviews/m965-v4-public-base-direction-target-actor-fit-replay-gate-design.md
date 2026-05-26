# m965-v4-public-base-direction-target-actor-fit-replay-gate-design Research Review

## Summary

- Generated at UTC: 20260526T053526Z
- Type: gate
- Gate tier: proof
- Promotion decision: direction_target_actor_fit_replay_gate_design_admit_m966
- Decision reason: M965 designs no-training public replay gate for M964 candidates including M267/M264 preflight six public surfaces behavior seeds and diagnostics

## Hypothesis

M964 candidate checkpoints need a no-training public replay gate before PPO or promotion decisions.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
- parent_dataset: docs/m964-v4-public-base-direction-target-actor-fit-objective-implementation.md, runs/m964_v4_public_base_direction_target_actor_fit/summary.json, runs/m964_v4_public_base_direction_target_actor_fit/route_decision.csv, runs/m964_v4_public_base_direction_target_actor_fit/candidate_checkpoints.csv
- parent_config: experiments/manifests/m964-v4-public-base-direction-target-actor-fit-objective-implementation.json
- parent_objective: design no-training replay gate for M964 direction-target actor-fit candidates
- derived_from: m964-v4-public-base-direction-target-actor-fit-objective-implementation
- blocked_by: M964 produced objective-level candidate checkpoints but no full replay/proof gate has been designed
- supersedes: None
- invalidates: promotion or PPO continuation before replay-gating M964 candidates

## Success Criteria

- design document exists
- candidate checkpoints are identified
- public replay surfaces are explicit
- behavior seeds are explicit
- pass/fail route logic is explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- design recommends promotion before replay gates
- design changes actor inputs
- design omits M267/M264 full surface
- design omits behavior seeds
- design runs PPO

## Evidence Gates

- M965 must not train
- M965 must not run PPO
- M965 must not promote
- M965 must preserve the P0 actor-input contract
- M965 must design public replay gates for M964 candidate checkpoints
- M965 must include M267/M264 full surface and behavior seeds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not run PPO
- do not accept target-fit metrics as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m965-v4-public-base-direction-target-actor-fit-replay-gate-design
- type: gate
- checkpoint: docs/m965-v4-public-base-direction-target-actor-fit-replay-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_actor_fit_replay_gate_design_admit_m966
- reason: M965 designs no-training public replay gate for M964 candidates including M267/M264 preflight six public surfaces behavior seeds and diagnostics

## Next Blocker

direction-target actor-fit replay gate has not been designed
