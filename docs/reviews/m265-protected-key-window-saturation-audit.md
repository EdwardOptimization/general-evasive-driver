# m265-protected-key-window-saturation-audit Research Review

## Summary

- Generated at UTC: 20260522T160906Z
- Type: gate
- Gate tier: proof
- Promotion decision: refresh_current_family_protected_surface
- Decision reason: M265 finds the old protected-key normal-margin window is saturated and blocks more PPO until a current-family protected surface is refreshed

## Hypothesis

The M263 to M264 repaired stage2 path has nearly saturated the single protected-key normal-margin window, so more PPO should be blocked until the protected surface or gate policy is refreshed.

## Lineage

- parent_checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: docs/m260-repair-disciplined-stage2-ppo-from-m259.md, docs/m261-repair-disciplined-stage2-repeat.md, docs/m262-stage2-repeat-fragility-audit.md, docs/m263-m261-raw-trajectory-projection-repair.md, docs/m264-repair-disciplined-stage2-repeat-from-m263.md
- parent_objective: audit whether the single protected key window is saturated before more PPO
- derived_from: m264-repair-disciplined-stage2-repeat-from-m263
- blocked_by: m264-repair-disciplined-stage2-repeat-from-m263
- supersedes: None
- invalidates: None

## Success Criteria

- M265 records the protected-key normal-margin trajectory and remaining slack
- M265 identifies whether the current blocker is protected-key saturation rather than replay, behavior, exact-source, or training instability
- M265 records a concrete next milestone decision without running new PPO
- actor input contract remains unchanged

## Failure Criteria

- audit artifacts are insufficient to explain the protected-key alpha collapse
- M265 starts new PPO or tunes from private holdout evidence
- actor input contract changes

## Evidence Gates

- compare protected-key normal-margin trajectory across M259 through M264
- compare exact-source improvement versus remaining protected-key slack
- separate replay or behavior regressions from protected-key window pressure
- decide whether another PPO repeat is admissible

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M265
- do not loosen the protected key without recorded evidence
- do not change actor inputs
- do not tune from private holdout evidence
- do not start medium PPO until the audit decision is recorded

## Failure Taxonomy

- protected_key_window_failure

## Scoreboard

- milestone: m265-protected-key-window-saturation-audit
- type: gate
- checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: refresh_current_family_protected_surface
- reason: M265 finds the old protected-key normal-margin window is saturated and blocks more PPO until a current-family protected surface is refreshed

## Next Blocker

m266-m264-family-protected-surface-refresh
