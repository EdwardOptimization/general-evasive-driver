# m251-checkpoint-interpolation-alpha-token-fix Research Review

## Summary

- Generated at UTC: 20260522T145656Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: complete_alpha_token_precision_fix
- Decision reason: M251 fixes checkpoint interpolation alpha label/path collisions for sub-0.001 sweeps and keeps common labels such as a125 and a500 stable

## Hypothesis

Checkpoint interpolation sweeps can safely support micro and nano alphas if labels and file tokens preserve enough significant decimal information to avoid collisions while retaining existing common-alpha labels.

## Lineage

- parent_checkpoint: runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
- parent_dataset: runs/m250_micro_m239_to_protected_source_interpolation
- parent_config: src/autodrift/checkpoint_interpolation.py
- parent_objective: unique checkpoint labels and paths for sub-0.001 alpha sweeps
- derived_from: m250-protected-key-source-actor-coupling-calibration
- blocked_by: m250-protected-key-source-actor-coupling-calibration
- supersedes: None
- invalidates: runs/m250_micro_m239_to_protected_source_interpolation

## Success Criteria

- 0.0001, 0.00025, and 0.0005 produce distinct policy labels and checkpoint paths
- legacy common alphas such as 0.125 and 0.5 keep their existing labels
- focused checkpoint interpolation tests pass
- research validator passes

## Failure Criteria

- sub-0.001 alphas still collide
- common alpha labels unnecessarily churn
- checkpoint interpolation semantics change
- PPO or driver promotion is run

## Evidence Gates

- focused checkpoint interpolation tests
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use rounded sub-0.001 alpha labels
- do not overwrite colliding checkpoint paths
- do not change checkpoint tensor interpolation semantics
- do not run PPO in M251

## Failure Taxonomy

- none

## Scoreboard

- milestone: m251-checkpoint-interpolation-alpha-token-fix
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: complete_alpha_token_precision_fix
- reason: M251 fixes checkpoint interpolation alpha label/path collisions for sub-0.001 sweeps and keeps common labels such as a125 and a500 stable

## Next Blocker

Map the alpha safety boundary around 0.00005 to 0.0001 with the fixed interpolation sweep before PPO from the calibrated base.
