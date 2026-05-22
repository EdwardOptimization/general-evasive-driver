# m291-row16-aware-guarded-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260522T195921Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: archive_m291_safe_interpolation_diagnostic_keep_m290_base
- Decision reason: Raw PPO loses M267/M264 drops and worsens exact M270 by 0.000503; alpha 0.1 passes full gates but still worsens exact M270 so M290 remains base

## Hypothesis

A smoke-scale guarded PPO continuation from m290x64_a500 can run without washing out the repeated row16-aware proof surfaces.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt, runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
- parent_dataset: runs/m289_row16_aware_balanced_repeat_calibration/anchors/row16_extra64_combined_anchor.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m290-row16-aware-balanced-repeat-fresh-seed.json, docs/m290-row16-aware-balanced-repeat-fresh-seed.md
- parent_objective: one smoke-scale guarded PPO continuation after repeatable row16-aware public-gate repair
- derived_from: m290-row16-aware-balanced-repeat-fresh-seed
- blocked_by: m290-row16-aware-balanced-repeat-fresh-seed
- supersedes: None
- invalidates: None

## Success Criteria

- raw or interpolated smoke PPO candidate preserves M183/M170 and M267/M264 first gates
- candidate passes full public replay protected-key and behavior gates before any promotion
- candidate does not require near-zero interpolation to be proof-safe
- actor input contract remains unchanged

## Failure Criteria

- PPO loses M183/M170 row16 or M267/M264 success drops
- protected-key guard no longer validates
- behavior seeds 9505 or 9506 regress
- safe interpolation collapses to near zero
- actor observation inputs change

## Evidence Gates

- run only smoke-scale PPO
- do not change actor inputs
- evaluate M183/M170 row16 and M267/M264 first
- run full replay protected-key and behavior gates only if first gates pass
- classify any proof-row or protected-key loss as proof_washout

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO in M291
- do not change actor observation inputs
- do not ignore M183/M170 row16 terminal margin
- do not ignore M267/M264 wrong-history retention
- do not promote raw PPO if interpolation is required but only near-zero alpha is safe

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m291-row16-aware-guarded-ppo-smoke
- type: driver_candidate
- checkpoint: runs/m291_row16_aware_guarded_ppo_smoke/interpolation/checkpoints/alpha_0_1.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844866
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: archive_m291_safe_interpolation_diagnostic_keep_m290_base
- reason: Raw PPO loses M267/M264 drops and worsens exact M270 by 0.000503; alpha 0.1 passes full gates but still worsens exact M270 so M290 remains base

## Next Blocker

m292-m291-ppo-proof-washout-audit
