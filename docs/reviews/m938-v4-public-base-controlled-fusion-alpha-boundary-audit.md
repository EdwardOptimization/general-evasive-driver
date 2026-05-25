# m938-v4-public-base-controlled-fusion-alpha-boundary-audit Research Review

## Summary

- Generated at UTC: 20260525T230517Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controlled_fusion_alpha_boundary_near_miss_route_to_boundary_objective_design
- Decision reason: M938 fine alpha sweep finds no exact overlap but alpha 0.15 is normal-retained and near the tail-lift deficit threshold so boundary-aware objective design is next

## Hypothesis

A finer no-training alpha sweep can determine whether M937's controlled-fusion raw direction has a narrow admissible overlap between normal retention and tail lift.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m937_v4_public_base_controlled_fusion_surface/checkpoints/raw_controlled_fusion_update.pt
- parent_dataset: docs/m937-v4-public-base-controlled-fusion-surface-implementation.md, runs/m937_v4_public_base_controlled_fusion_surface/summary.json, runs/m937_v4_public_base_controlled_fusion_surface/alpha_metrics.csv
- parent_config: experiments/manifests/m937-v4-public-base-controlled-fusion-surface-implementation.json
- parent_objective: no-training fine alpha boundary audit of the M937 raw controlled-fusion direction
- derived_from: m937-v4-public-base-controlled-fusion-surface-implementation
- blocked_by: M937 raw controlled-fusion direction has not been evaluated on a fine boundary alpha grid
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- training_started is false
- base and raw checkpoints differ only on actor_mean and response_context_fusion.0
- sample_reconstruction_success_rate >= 0.98
- fine alpha grid includes values between 0.10 and 0.35
- route decision is recorded without replay PPO or promotion

## Failure Criteria

- M938 starts training
- base and raw checkpoints differ outside allowed controlled surface
- actor input contract changes
- M938 runs replay PPO or promotion

## Evidence Gates

- M938 must be no-training
- M938 must compare M399 base to M937 raw controlled-fusion direction
- M938 must preserve P0 actor input contract
- M938 must keep replay PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M938
- do not change actor inputs
- do not update checkpoints
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m938-v4-public-base-controlled-fusion-alpha-boundary-audit
- type: infrastructure
- checkpoint: runs/m938_v4_public_base_controlled_fusion_alpha_boundary/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_alpha_boundary_near_miss_route_to_boundary_objective_design
- reason: M938 fine alpha sweep finds no exact overlap but alpha 0.15 is normal-retained and near the tail-lift deficit threshold so boundary-aware objective design is next

## Next Blocker

M937 raw controlled-fusion direction has not been evaluated on a fine boundary alpha grid
