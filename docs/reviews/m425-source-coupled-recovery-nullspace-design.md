# m425-source-coupled-recovery-nullspace-design Research Review

## Summary

- Generated at UTC: 20260523T173555Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m426_source_coupled_nullspace_implementation
- Decision reason: M425 designs projected recovery-gradient tooling so M398 recovery utility can move only in directions that do not first-order damage exact gates M267 rows 6 and 15 or old-key 10023

## Hypothesis

A source-coupled recovery/nullspace residual can target old-key recovery rows while keeping M267 rows 6 and 15 plus old-key 10023 as active constraints, unlike radius-only profiles that trade utility for proof loss.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m422_mixed_radius_anchor/mixed_b_radius_anchor.npz, runs/m423_mixed_b_projection_ltraj1e13_s40_seed10154, runs/m423_mixed_c_projection_ltraj1e13_s40_seed10155
- parent_config: experiments/manifests/m424-mixed-radius-utility-ceiling-audit.json
- parent_objective: design a source-coupled recovery utility residual after radius-only utility ceiling
- derived_from: m424-mixed-radius-utility-ceiling-audit
- blocked_by: m424-mixed-radius-utility-ceiling-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define hard active constraints for M267 rows 6 and 15 and old-key 10023
- define a recovery merit tied to M398 recovery targets without relaxing hard constraints
- define candidate selection order with exact gates before replay gates before utility
- pre-register a no-PPO implementation/probe path

## Failure Criteria

- design is equivalent to another per-source radius tweak
- design admits PPO directly
- design changes actor inputs or outputs
- design removes old-key or M267 diagnostics

## Evidence Gates

- no PPO run
- no checkpoint promotion
- no actor input/output change
- identify hard constraints M267 rows 6 and 15 plus old-key 10023
- design a recovery merit that cannot loosen those hard constraints implicitly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m425-source-coupled-recovery-nullspace-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m426_source_coupled_nullspace_implementation
- reason: M425 designs projected recovery-gradient tooling so M398 recovery utility can move only in directions that do not first-order damage exact gates M267 rows 6 and 15 or old-key 10023

## Next Blocker

m426-source-coupled-nullspace-implementation
