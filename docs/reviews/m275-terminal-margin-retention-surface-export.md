# m275-terminal-margin-retention-surface-export Research Review

## Summary

- Generated at UTC: 20260522T181348Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_terminal_margin_anchored_actor_update
- Decision reason: M275 exports 30 fragile rows and 1440 retention trajectory-anchor rows from the M272 current base with M183/M170 row16 included and validated through the existing loader

## Hypothesis

A refreshed current-base terminal-margin retention surface can represent fragile closed-loop rows in a reusable registry and trajectory-anchor format, enabling the next guarded update to protect row16 explicitly.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m273_m272_boundary_trust_region_audit/row16_alpha_audit.csv, runs/m272_selected_m183_m168_replay_gate/boundary_replay_rows.csv, runs/m272_selected_m183_m170_replay_gate/boundary_replay_rows.csv, runs/m272_selected_m193_m189_replay_gate/boundary_replay_rows.csv, runs/m272_selected_m212_m204_replay_gate/boundary_replay_rows.csv, runs/m272_selected_m223_m219_replay_gate/boundary_replay_rows.csv, runs/m272_selected_m267_m264_replay_gate/boundary_replay_rows.csv
- parent_config: experiments/manifests/m274-terminal-margin-retention-design.json, docs/m274-terminal-margin-retention-design.md
- parent_objective: export terminal-margin retention surface before any further learning
- derived_from: m274-terminal-margin-retention-design
- blocked_by: m274-terminal-margin-retention-design
- supersedes: None
- invalidates: None

## Success Criteria

- fragile_rows.csv includes M183/M170 row16
- terminal_margin_registry.csv records baseline normal margin, hard floor, allowed regression, and row source
- retention_trajectory_anchor.npz loads through the existing trajectory anchor loader
- recovery_trajectory_anchor.npz is exported or explicitly marked unavailable with a reason
- summary.json records row counts and weight ranges
- no PPO or actor update is run

## Failure Criteria

- row16 is missing
- NPZ fails TrajectoryActionAnchor validation
- export relies on hidden params or privileged actor inputs
- PPO or actor update is run

## Evidence Gates

- export fragile row registry
- export retention trajectory anchor
- export recovery trajectory anchor when source trajectories are available
- validate TrajectoryActionAnchor NPZ shape contract
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M275
- do not run a new actor update in M275
- do not omit M183/M170 row16
- do not include privileged actor inputs
- do not claim driver promotion

## Failure Taxonomy

- none

## Scoreboard

- milestone: m275-terminal-margin-retention-surface-export
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_terminal_margin_anchored_actor_update
- reason: M275 exports 30 fragile rows and 1440 retention trajectory-anchor rows from the M272 current base with M183/M170 row16 included and validated through the existing loader

## Next Blocker

m276-terminal-margin-anchored-actor-update
