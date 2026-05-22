# m247-source-balanced-outcome-loss-implementation Research Review

## Summary

- Generated at UTC: 20260522T143123Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_source_balanced_ppo_smoke_from_m239
- Decision reason: M247 adds named source-balanced outcome losses to PPO config/training and per-source metrics; focused tests passed and no PPO was run

## Hypothesis

Adding named source-balanced outcome intervention losses will let the next PPO smoke apply explicit protected-key pressure instead of relying on one combined M232 loss.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
- parent_config: configs/ppo_m243_exact_gated_from_m239_smoke.json
- parent_objective: source-balanced outcome intervention auxiliary losses, M245 source-aware exact gate
- derived_from: m246-source-balanced-outcome-loss-design
- blocked_by: m246-source-balanced-outcome-loss-design
- supersedes: None
- invalidates: None

## Success Criteria

- add PPO config support for multiple named source outcome losses
- load and validate each source NPZ independently
- add each source loss to the PPO objective with its own coefficient
- log per-source outcome loss metrics
- add focused tests for validation and logging
- do not run PPO

## Failure Criteria

- source loss config silently accepts missing or duplicate names
- per-source loss metrics are not logged
- existing combined outcome loss tests regress
- run PPO or modify actor inputs

## Evidence Gates

- source-balanced outcome loss focused tests
- PPO config validation tests
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M247
- do not change actor inputs
- do not loosen source-aware exact gates
- do not remove existing combined outcome loss compatibility

## Failure Taxonomy

- none

## Scoreboard

- milestone: m247-source-balanced-outcome-loss-implementation
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_source_balanced_ppo_smoke_from_m239
- reason: M247 adds named source-balanced outcome losses to PPO config/training and per-source metrics; focused tests passed and no PPO was run

## Next Blocker

Run one source-balanced PPO smoke from M239.
