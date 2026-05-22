# m260-repair-disciplined-stage2-ppo-from-m259 Research Review

## Summary

- Generated at UTC: 20260522T154348Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m260_a050_public_gate_base
- Decision reason: M260 4096-step stage2 raw PPO improves exact sources but full raw fails protected key; alpha 0.05 passes exact source row16 replay protected-key and behavior gates

## Hypothesis

After M258 and M259, a short staged PPO escalation can make additional progress if every PPO update is followed by exact-source gating and trajectory-anchored projection repair before promotion.

## Lineage

- parent_checkpoint: runs/m259_m258_to_projection_interpolation/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m259-trajectory-anchored-repair-repeat.md
- parent_objective: first staged PPO escalation after two positive trajectory-anchored repair smokes
- derived_from: m259-trajectory-anchored-repair-repeat
- blocked_by: m259-trajectory-anchored-repair-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- stage2 PPO completes without actor input changes
- raw PPO or repaired projection has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus M259
- at least one exact-gated interpolation alpha preserves M183/M170 row16
- selected candidate passes full public replay, protected-key, and behavior gates
- no long PPO is run

## Failure Criteria

- stage2 PPO cannot be repaired without losing source improvement
- trajectory-anchored projection repairs exact sources but breaks row16
- candidate passes row16 but fails broader public replay, protected-key, or behavior gates
- training instability appears
- actor input contract changes

## Evidence Gates

- short stage2 PPO only
- raw PPO exact source gate
- trajectory-anchored projection repair if protected source regresses
- interpolation from M259
- row16 gate before full public gates
- full public replay protected-key and behavior gates only after exact source and row16 pass
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run long PPO in M260
- do not promote raw PPO with protected-key source regression
- do not skip exact-source or row16 gates
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m260-repair-disciplined-stage2-ppo-from-m259
- type: driver_candidate
- checkpoint: runs/m260_m259_to_raw_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m260_a050_public_gate_base
- reason: M260 4096-step stage2 raw PPO improves exact sources but full raw fails protected key; alpha 0.05 passes exact source row16 replay protected-key and behavior gates

## Next Blocker

m261-repair-disciplined-stage2-repeat
