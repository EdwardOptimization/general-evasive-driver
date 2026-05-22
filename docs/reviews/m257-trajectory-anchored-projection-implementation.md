# m257-trajectory-anchored-projection-implementation Research Review

## Summary

- Generated at UTC: 20260522T152126Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: complete_trajectory_anchor_projection_support
- Decision reason: M257 adds trajectory action anchor support to outcome_intervention_optimize with focused tests and a real M235 anchor optimizer smoke; no PPO and no driver promotion

## Hypothesis

Post-PPO projection needs trajectory action anchor support so protected-source repair can also preserve fragile closed-loop rows such as M183/M170 row16.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/m256_post_ppo_protected_source_projection_seed10067/optimized_checkpoint.pt
- parent_dataset: runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz, runs/m256_m183_m170_replay_gate_a0_00001/comparison_summary.csv
- parent_config: src/autodrift/outcome_intervention_optimize.py, docs/m256-post-ppo-protected-source-projection.md
- parent_objective: allow post-PPO projection to protect fragile closed-loop trajectory anchors
- derived_from: m256-post-ppo-protected-source-projection
- blocked_by: m256-post-ppo-protected-source-projection
- supersedes: None
- invalidates: None

## Success Criteria

- outcome_intervention_optimize can load trajectory_action_anchor_snapshot_npz
- projection loss logs trajectory_action_anchor_loss when enabled
- focused tests cover the new optimizer path
- research validator passes
- no PPO is run

## Failure Criteria

- trajectory anchor support changes train_ppo behavior
- optimizer cannot load the existing M235 trajectory anchor
- tests fail
- actor input contract changes

## Evidence Gates

- trajectory anchor support in outcome_intervention_optimize
- focused tests
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M257
- do not change actor inputs
- do not alter existing trajectory anchor semantics in train_ppo
- do not promote a driver checkpoint in an infrastructure milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m257-trajectory-anchored-projection-implementation
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: complete_trajectory_anchor_projection_support
- reason: M257 adds trajectory action anchor support to outcome_intervention_optimize with focused tests and a real M235 anchor optimizer smoke; no PPO and no driver promotion

## Next Blocker

m258-trajectory-anchored-projection-retry
