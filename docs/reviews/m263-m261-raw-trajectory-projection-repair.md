# m263-m261-raw-trajectory-projection-repair Research Review

## Summary

- Generated at UTC: 20260522T160147Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m263_a005_public_gate_base
- Decision reason: M263 repairs M261 raw protected-source regression with trajectory projection and promotes alpha 0.005 after exact source replay protected-key and behavior gates

## Hypothesis

A trajectory-anchored protected-source projection can repair M261 raw PPO's protected-key source regression and admit a larger proof-safe update than M261 alpha 0.001.

## Lineage

- parent_checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt, runs/ppo_m261_stage2_repeat_from_m260_seed5228/checkpoint.pt
- parent_dataset: runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m261-repair-disciplined-stage2-repeat.md, docs/m262-stage2-repeat-fragility-audit.md
- parent_objective: repair M261 raw protected-key source regression without running PPO
- derived_from: m261-repair-disciplined-stage2-repeat, m262-stage2-repeat-fragility-audit
- blocked_by: m262-stage2-repeat-fragility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- projection completes from M261 raw without actor input changes
- projected checkpoint improves protected-key source and M223 source relative to M261 base or admits an interpolation candidate that does
- selected interpolation candidate passes exact-source tolerance versus M261 base
- selected candidate preserves M183/M170 row16
- selected candidate passes full public replay, protected-key, and behavior gates
- no PPO is run

## Failure Criteria

- projection cannot repair protected-key source without breaking M223 source
- all exact-gated interpolation candidates fail row16 or protected key
- selected candidate fails broader public replay or behavior gates
- actor input contract changes

## Evidence Gates

- no new PPO
- trajectory-anchored protected-source projection from M261 raw
- exact source gate versus M261 base
- interpolation from M261 base to repaired projection
- row16 gate before full public gates
- protected key boundary check
- full public replay and behavior gates
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M263
- do not promote raw M261
- do not skip trajectory anchor
- do not skip exact-source or row16 gates
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m263-m261-raw-trajectory-projection-repair
- type: driver_candidate
- checkpoint: runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m263_a005_public_gate_base
- reason: M263 repairs M261 raw protected-source regression with trajectory projection and promotes alpha 0.005 after exact source replay protected-key and behavior gates

## Next Blocker

m264-repair-disciplined-stage2-repeat-from-m263
