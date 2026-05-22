# m266-m264-family-protected-surface-refresh Research Review

## Summary

- Generated at UTC: 20260522T171737Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_protected_surface_objective_conversion
- Decision reason: M266 finds 180 source-diverse wrong-history boundary rows across 13 physical pairs 8 steps 3 checkpoints and 2 targets so old key remains diagnostic but not sole protected-surface veto

## Hypothesis

A current-family protected-surface refresh can determine whether M264's protected-key saturation is a single-key artifact or a broader proof-surface constraint.

## Lineage

- parent_checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt, runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt, runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: docs/m265-protected-key-window-saturation-audit.md
- parent_objective: refresh current-family protected rows before more PPO because the old single key is saturated
- derived_from: m265-protected-key-window-saturation-audit
- blocked_by: m265-protected-key-window-saturation-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M266 mines or audits current-family protected candidates without PPO
- M266 reports accepted wrong-history rows and diversity metrics
- M266 records whether the old protected key is representative, stale, or saturated
- M266 records a concrete next milestone decision before more PPO
- actor input contract remains unchanged

## Failure Criteria

- candidate surface is duplicate-dominated or has zero accepted wrong-history outcome rows
- audit cannot distinguish single-key saturation from broader proof loss
- M266 starts PPO or changes actor inputs

## Evidence Gates

- mine current-family protected surface candidates around M263 and M264
- check source diversity across seeds physical pairs and margin buckets
- require wrong-history outcome sensitivity rather than only action distance
- do not admit PPO from a duplicate-dominated surface
- record whether old protected key is representative or saturated

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M266
- do not loosen the old protected key without evidence
- do not change actor inputs
- do not tune from private holdout evidence
- do not promote a checkpoint in M266

## Failure Taxonomy

- none

## Scoreboard

- milestone: m266-m264-family-protected-surface-refresh
- type: gate
- checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: admit_protected_surface_objective_conversion
- reason: M266 finds 180 source-diverse wrong-history boundary rows across 13 physical pairs 8 steps 3 checkpoints and 2 targets so old key remains diagnostic but not sole protected-surface veto

## Next Blocker

m267-protected-surface-objective-replay-conversion
