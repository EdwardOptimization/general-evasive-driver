# m964-v4-public-base-direction-target-actor-fit-objective-implementation Research Review

## Summary

- Generated at UTC: 20260526T050655Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: direction_target_actor_fit_candidate_route_to_replay_gate_design
- Decision reason: M964 objective-only actor_mean fit produces 5 candidate alphas; alpha 1.0 best improves direction-target MSE while M267 active proof and retention pass

## Hypothesis

An objective-only actor-fit update can reduce M962 direction-target loss while preserving M267/M264 proof preflight and retention anchors.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m963-v4-public-base-target-feasibility-export-branch-synthesis.md, runs/m962_v4_public_base_direction_target_export/summary.json, runs/m962_v4_public_base_direction_target_export/accepted_direction_targets.csv, runs/m962_v4_public_base_direction_target_export/direction_target_family_catalog.csv, runs/m962_v4_public_base_direction_target_export/branch_separated_proof_targets.csv, runs/m962_v4_public_base_direction_target_export/retention_anchor_targets.csv
- parent_config: experiments/manifests/m963-v4-public-base-target-feasibility-export-branch-synthesis.json
- parent_objective: run first objective-only actor-fit probe on M962 exported direction-target corpus
- derived_from: m963-v4-public-base-target-feasibility-export-branch-synthesis, m962-v4-public-base-direction-target-export-implementation
- blocked_by: M962 exported targets but no actor-fit probe has tested whether the actor can fit them without proof washout
- supersedes: None
- invalidates: PPO or promotion before objective-only direction-target actor-fit gate

## Success Criteria

- summary artifact exists
- target-fit metrics are written
- proof-anchor metrics are written
- retention-anchor metrics are written
- M267/M264 preflight is written
- interpolation candidates are evaluated
- PPO and promotion remain blocked

## Failure Criteria

- implementation runs PPO
- implementation changes actor inputs
- implementation trains diagnostic-only target families
- implementation omits proof-anchor or retention metrics
- implementation promotes a checkpoint

## Evidence Gates

- M964 must not run PPO
- M964 must not promote
- M964 must preserve the P0 actor-input contract
- M964 must start from the M399 public base
- M964 must use M962 exported targets
- M964 must report exact target-fit metrics and M267/M264 proof preflight

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change actor inputs
- do not use private holdout
- do not promote
- do not run PPO
- do not train diagnostic-only anti-aligned target families
- do not collapse wrong-history proof anchors into normal safe targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m964-v4-public-base-direction-target-actor-fit-objective-implementation
- type: infrastructure
- checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_actor_fit_candidate_route_to_replay_gate_design
- reason: M964 objective-only actor_mean fit produces 5 candidate alphas; alpha 1.0 best improves direction-target MSE while M267 active proof and retention pass

## Next Blocker

direction-target actor-fit objective has not been implemented
