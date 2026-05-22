# m276-terminal-margin-anchored-actor-update Research Review

## Summary

- Generated at UTC: 20260522T181904Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_terminal_margin_retention_anchor_update
- Decision reason: M276 improves sampled/exact M270 objective but fails M183/M170 row16; only alpha 0.0002 is row16-safe and the objective movement is negligible

## Hypothesis

The M275 terminal-margin trajectory anchor can let a small M270 actor-coupling update improve objective without crossing the M183/M170 row16 terminal-margin cliff.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz, runs/m275_terminal_margin_retention_surface/terminal_margin_registry.csv
- parent_config: experiments/manifests/m275-terminal-margin-retention-surface-export.json, docs/m275-terminal-margin-retention-surface-export.md
- parent_objective: M270 source-balanced objective plus M275 terminal-margin retention anchor
- derived_from: m275-terminal-margin-retention-surface-export
- blocked_by: m275-terminal-margin-retention-surface-export
- supersedes: None
- invalidates: None

## Success Criteria

- start from m272b_a0_01025
- use M270 source-balanced objective and M275 retention trajectory anchor
- run exactly one small actor update before any repeat or PPO
- improve fixed M270 objective versus M272
- preserve M183/M170 row16 terminal margin above the registered required floor
- preserve all six replay surfaces, protected key, and behavior seeds if row16 passes
- actor input contract remains unchanged

## Failure Criteria

- row16 terminal margin crosses the registered floor
- combined objective improves but row16 or replay surfaces regress
- retention anchor prevents any objective improvement
- PPO is run
- actor observation inputs change

## Evidence Gates

- fixed sampled and exact M270 objective improvement
- M183/M170 row16 terminal-margin hard gate
- six replay surfaces if row16 passes
- old protected-key diagnostic if replay passes
- behavior seeds 9505 and 9506 if replay passes
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M276
- do not run multiple actor-update seeds before the first seed passes
- do not skip M183/M170 row16
- do not promote based only on objective improvement
- do not change actor inputs

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m276-terminal-margin-anchored-actor-update
- type: driver_candidate
- checkpoint: runs/m276_m272_actor_coupling_m270_terminal_margin_anchor100_s10_lr5e5_seed10075/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_terminal_margin_retention_anchor_update
- reason: M276 improves sampled/exact M270 objective but fails M183/M170 row16; only alpha 0.0002 is row16-safe and the objective movement is negligible

## Next Blocker

m277-terminal-margin-recovery-anchor-design
