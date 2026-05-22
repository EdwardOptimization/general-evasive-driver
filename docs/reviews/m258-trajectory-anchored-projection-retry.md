# m258-trajectory-anchored-projection-retry Research Review

## Summary

- Generated at UTC: 20260522T153004Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m258_a010_public_gate_base
- Decision reason: M258 trajectory-anchored projection repairs protected-key source while retaining row16 full replay protected-key and behavior gates; promote m258_a010 as public-gate base

## Hypothesis

Adding the M235 trajectory action anchor to the M256 protected-source projection can preserve row16 closed-loop behavior while still repairing protected-key source loss from M254 raw PPO.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz, runs/m256_m183_m170_replay_gate_a0_00001/comparison_summary.csv
- parent_config: src/autodrift/outcome_intervention_optimize.py, docs/m256-post-ppo-protected-source-projection.md, docs/m257-trajectory-anchored-projection-implementation.md
- parent_objective: post-PPO protected-key source projection with trajectory action anchor retention
- derived_from: m256-post-ppo-protected-source-projection, m257-trajectory-anchored-projection-implementation
- blocked_by: m257-trajectory-anchored-projection-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- projection reduces protected-key source loss versus M254 raw
- at least one projected/interpolated alpha has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus M253
- at least one exact-gated alpha preserves M183/M170 row16 normal success and margin
- only row16/exact-gated candidates advance to full replay protected-key and behavior gates
- no PPO is run

## Failure Criteria

- trajectory-anchored projection cannot restore protected-key source without losing M223 improvement
- all projected/interpolated candidates fail exact source gate
- exact-gated candidates still fail M183/M170 row16
- candidate exact-gates and row16-gates but fails broader public proof retention
- actor input contract changes

## Evidence Gates

- M245 exact source-aware objective gate
- M183/M170 row16 replay retention
- full public replay gates only after exact source and row16 gates pass
- protected key gate only after exact source and row16 gates pass
- behavior retention only after proof gates pass
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M258
- do not promote projection without exact source and public proof gates
- do not run full public gates if exact source or row16 gate fails
- do not change actor inputs
- do not alter trajectory anchor format

## Failure Taxonomy

- none

## Scoreboard

- milestone: m258-trajectory-anchored-projection-retry
- type: driver_candidate
- checkpoint: runs/m258_m253_to_projection_interpolation/checkpoints/alpha_0_01.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844114
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m258_a010_public_gate_base
- reason: M258 trajectory-anchored projection repairs protected-key source while retaining row16 full replay protected-key and behavior gates; promote m258_a010 as public-gate base

## Next Blocker

m259-trajectory-anchored-repair-repeat
