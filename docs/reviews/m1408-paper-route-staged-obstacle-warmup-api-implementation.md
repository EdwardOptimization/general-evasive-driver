# m1408-paper-route-staged-obstacle-warmup-api-implementation Research Review

## Summary

- Generated at UTC: 20260529T002915Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: staged_obstacle_warmup_api_implemented_route_to_branch_synthesis_before_source_smoke
- Decision reason: M1408 implements disabled-by-default staged slot0 warmup gate API with focused and full tests passing and routes to branch synthesis before source smoke

## Hypothesis

A disabled-by-default staged warmup gate API can be added while preserving default env behavior and the actor input contract.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1407-paper-route-pre-emergency-gate-stimulus-design.md, docs/m1406-paper-route-mild-warmup-outcome-result-audit.md
- parent_config: experiments/manifests/m1407-paper-route-pre-emergency-gate-stimulus-design.json
- parent_objective: implement a disabled-by-default staged warmup gate API with tests
- derived_from: m1407-paper-route-pre-emergency-gate-stimulus-design
- blocked_by: M1407 requires task API support before a pre-emergency gate source smoke
- supersedes: running another figure-eight-only source smoke, training from M1405 reset-only rows
- invalidates: None

## Success Criteria

- WarmupGateConfig or equivalent disabled-by-default config exists
- default env observation shape and default obstacle behavior remain unchanged
- tests cover warmup gate visibility, switch to emergency obstacle, finite diagnostics, and unchanged observation shape
- result chooses next route without source smoke, outcome intervention, training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- default env behavior changes unexpectedly
- actor observation shape changes unexpectedly
- warmup gate requires actor oracle labels or scripted commands
- tests are missing
- result routes directly to training or claim expansion

## Evidence Gates

- M1408 must implement disabled-by-default staged warmup gate support with tests
- M1408 must keep default env behavior unchanged
- M1408 must keep actor observation shape and P0 human-view contract unchanged for the mainline config
- M1408 must not train, run PPO, run source smoke, run outcome interventions, promote, use private holdout, or export a training corpus

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source smoke
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not export corpus
- do not add actor oracle labels
- do not add scripted controller commands
- do not change default actor input dimensionality

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1408-paper-route-staged-obstacle-warmup-api-implementation
- type: infrastructure
- checkpoint: tests/test_env.py
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: staged_obstacle_warmup_api_implemented_route_to_branch_synthesis_before_source_smoke
- reason: M1408 implements disabled-by-default staged slot0 warmup gate API with focused and full tests passing and routes to branch synthesis before source smoke

## Next Blocker

m1409-paper-route-warmup-reveal-pressure-branch-synthesis
