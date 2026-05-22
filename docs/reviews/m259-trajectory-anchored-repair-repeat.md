# m259-trajectory-anchored-repair-repeat Research Review

## Summary

- Generated at UTC: 20260522T153537Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m259_a010_public_gate_base
- Decision reason: M259 repeats the PPO protected-source conflict and trajectory-anchored repair on fresh seed5226 then passes exact source row16 full replay protected-key and behavior gates

## Hypothesis

The M258 trajectory-anchored post-PPO repair pattern is repeatable on a fresh PPO seed and not just a lucky repair of M254 seed5225.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/m258_m253_to_projection_interpolation/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, src/autodrift/outcome_intervention_optimize.py, docs/m258-trajectory-anchored-projection-retry.md
- parent_objective: repeat the PPO plus trajectory-anchored post-PPO repair path on a fresh seed before longer continuation
- derived_from: m258-trajectory-anchored-projection-retry
- blocked_by: m258-trajectory-anchored-projection-retry
- supersedes: None
- invalidates: None

## Success Criteria

- fresh PPO smoke completes without actor input changes
- raw PPO or its trajectory-anchored projection has M223 source delta < 0, aggregate M232 delta <= +1e-8, and protected-key source delta <= +1e-8 versus the latest public-gate base
- at least one exact-gated interpolation alpha preserves M183/M170 row16
- the selected candidate passes full public replay, protected-key, and behavior gates
- no long PPO is run

## Failure Criteria

- fresh PPO update direction cannot be repaired without losing source improvement
- trajectory-anchored projection repairs exact sources but still breaks row16
- candidate passes row16 but fails broader public replay, protected-key, or behavior gates
- training is seed-fragile or unstable
- actor input contract changes

## Evidence Gates

- fresh-seed PPO smoke from the current public-gate base or M253 lineage base
- post-PPO exact source gate
- trajectory-anchored projection repair if protected source regresses
- interpolation from latest public-gate base
- full public replay gates only after exact source and row16 gates pass
- protected key and behavior retention
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lengthen PPO in M259
- do not promote a raw PPO checkpoint that regresses protected-key source
- do not run broad public gates before exact source and row16 gates
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m259-trajectory-anchored-repair-repeat
- type: driver_candidate
- checkpoint: runs/m259_m258_to_projection_interpolation/checkpoints/alpha_0_01.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844119
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m259_a010_public_gate_base
- reason: M259 repeats the PPO protected-source conflict and trajectory-anchored repair on fresh seed5226 then passes exact source row16 full replay protected-key and behavior gates

## Next Blocker

m260-repair-disciplined-stage2-ppo-from-m259
