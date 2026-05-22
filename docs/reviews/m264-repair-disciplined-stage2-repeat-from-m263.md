# m264-repair-disciplined-stage2-repeat-from-m263 Research Review

## Summary

- Generated at UTC: 20260522T160706Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m264_a001_public_gate_base
- Decision reason: M264 raw exact sources improve and alpha 0.001 passes replay protected-key and behavior gates but protected-key slack is only 0.000029

## Hypothesis

The repaired stage2 PPO discipline can repeat from M263 on a fresh seed when raw PPO is followed by exact-source gating and trajectory-anchored projection repair before promotion.

## Lineage

- parent_checkpoint: runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m263-m261-raw-trajectory-projection-repair.md
- parent_objective: repeat the repaired stage2 PPO discipline from the M263 public-gate base
- derived_from: m263-m261-raw-trajectory-projection-repair
- blocked_by: m263-m261-raw-trajectory-projection-repair
- supersedes: None
- invalidates: None

## Success Criteria

- fresh 4096-step PPO completes without actor input changes
- raw PPO or its trajectory-anchored projection has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus M263
- selected interpolation candidate preserves M183/M170 row16
- selected candidate passes full public replay, protected-key, and behavior gates
- no medium or long PPO is run

## Failure Criteria

- fresh PPO update direction cannot be repaired without losing source improvement
- trajectory-anchored projection repairs exact sources but breaks row16
- candidate passes row16 but fails broader public replay, protected-key, or behavior gates
- training instability appears
- actor input contract changes

## Evidence Gates

- fresh-seed 4096-step PPO from M263
- raw PPO exact source gate
- trajectory-anchored projection repair if protected source regresses or protected key fails
- interpolation from M263 base
- row16 gate before full public gates
- protected key boundary check
- full public replay and behavior gates
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO in M264
- do not promote raw PPO that fails protected-key source or protected-key replay
- do not skip trajectory-anchored repair if raw PPO is unsafe
- do not skip exact-source or row16 gates
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m264-repair-disciplined-stage2-repeat-from-m263
- type: driver_candidate
- checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m264_a001_public_gate_base
- reason: M264 raw exact sources improve and alpha 0.001 passes replay protected-key and behavior gates but protected-key slack is only 0.000029

## Next Blocker

m265-protected-key-window-saturation-audit
