# m261-repair-disciplined-stage2-repeat Research Review

## Summary

- Generated at UTC: 20260522T155145Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m261_a001_public_gate_base
- Decision reason: M261 repeat raw PPO improves M223 but regresses protected-key source; alpha 0.001 passes exact source row16 replay protected-key and behavior gates while exposing stage2 seed fragility

## Hypothesis

The M260 4096-step staged PPO improvement is repeatable on a fresh seed if promotion remains interpolation-gated by exact source, row16, and protected-key retention.

## Lineage

- parent_checkpoint: runs/m260_m259_to_raw_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m260-repair-disciplined-stage2-ppo-from-m259.md
- parent_objective: repeat the short staged PPO escalation after M260 single-seed success
- derived_from: m260-repair-disciplined-stage2-ppo-from-m259
- blocked_by: m260-repair-disciplined-stage2-ppo-from-m259
- supersedes: None
- invalidates: None

## Success Criteria

- fresh 4096-step PPO completes without actor input changes
- raw PPO or an interpolated candidate has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus M260
- at least one exact-gated interpolation alpha preserves M183/M170 row16
- selected candidate passes full public replay, protected-key, and behavior gates
- no longer PPO is run

## Failure Criteria

- fresh stage2 PPO cannot improve exact sources
- all exact-gated candidates fail row16 or protected key
- selected candidate fails broader public replay or behavior gates
- training instability appears
- actor input contract changes

## Evidence Gates

- fresh-seed 4096-step PPO stage2
- raw PPO exact source gate
- interpolation from M260
- row16 gate before full public gates
- protected key boundary check
- full public replay and behavior gates
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lengthen PPO beyond the M260 stage2 size
- do not promote a raw checkpoint that fails protected key
- do not skip interpolation boundary search
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m261-repair-disciplined-stage2-repeat
- type: driver_candidate
- checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m261_a001_public_gate_base
- reason: M261 repeat raw PPO improves M223 but regresses protected-key source; alpha 0.001 passes exact source row16 replay protected-key and behavior gates while exposing stage2 seed fragility

## Next Blocker

m262-stage2-repeat-fragility-audit
