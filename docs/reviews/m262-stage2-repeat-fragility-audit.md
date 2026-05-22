# m262-stage2-repeat-fragility-audit Research Review

## Summary

- Generated at UTC: 20260522T155441Z
- Type: gate
- Gate tier: proof
- Promotion decision: repair_with_m261_raw_trajectory_projection
- Decision reason: M262 finds M261 safe-alpha collapse is not replay or behavior regression but seed-fragile protected-source direction and protected-key normal-margin pressure

## Hypothesis

M261 passed promotion only at a tiny interpolation alpha because the repeated stage2 PPO direction is seed-fragile and remains constrained by protected-key source and normal-margin pressure.

## Lineage

- parent_checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m260-repair-disciplined-stage2-ppo-from-m259.md, docs/m261-repair-disciplined-stage2-repeat.md
- parent_objective: audit whether M260/M261 staged PPO repeats are stable enough to admit medium PPO
- derived_from: m260-repair-disciplined-stage2-ppo-from-m259, m261-repair-disciplined-stage2-repeat
- blocked_by: m261-repair-disciplined-stage2-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- M262 produces a source-aware comparison of M260 and M261 raw PPO movement
- M262 identifies whether the limiting gate is exact protected-source regression, protected-key normal-margin pressure, replay row16 fragility, behavior regression, or training instability
- M262 records a concrete next milestone decision without running new PPO
- actor input contract remains unchanged

## Failure Criteria

- audit artifacts are insufficient to explain the M260 versus M261 safe-alpha gap
- M262 starts new PPO or tunes from private holdout evidence
- actor input contract changes

## Evidence Gates

- compare M260 and M261 raw exact-source movement
- compare safe interpolation alpha boundaries
- compare protected-key normal-margin pressure
- compare behavior retention deltas
- classify the next blocker before any medium PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M262
- do not promote a new checkpoint in M262
- do not change actor inputs
- do not use private holdout evidence
- do not start medium PPO until the audit decision is recorded

## Failure Taxonomy

- seed_fragility
- protected_key_window_failure

## Scoreboard

- milestone: m262-stage2-repeat-fragility-audit
- type: gate
- checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: repair_with_m261_raw_trajectory_projection
- reason: M262 finds M261 safe-alpha collapse is not replay or behavior regression but seed-fragile protected-source direction and protected-key normal-margin pressure

## Next Blocker

m263-m261-raw-trajectory-projection-repair
