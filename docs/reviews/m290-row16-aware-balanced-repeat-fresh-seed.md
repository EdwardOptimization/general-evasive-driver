# m290-row16-aware-balanced-repeat-fresh-seed Research Review

## Summary

- Generated at UTC: 20260522T195048Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m290x64_a500_and_admit_ppo_smoke
- Decision reason: Fresh seed repeats row16-aware recipe with alpha 0.5 exact M270 delta -0.002097 and passes six replay surfaces protected key behavior gates; admit smoke-scale PPO only

## Hypothesis

The M289 row16-aware extra64 recipe should repeat on a fresh optimizer seed with a proof-safe non-micro interpolation, making PPO smoke admission plausible.

## Lineage

- parent_checkpoint: runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
- parent_dataset: runs/m289_row16_aware_balanced_repeat_calibration/anchors/row16_extra64_combined_anchor.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m289-row16-aware-balanced-repeat-calibration.json, docs/m289-row16-aware-balanced-repeat-calibration.md
- parent_objective: repeat M289 row16-aware extra64 balanced recipe on a fresh optimizer seed
- derived_from: m289-row16-aware-balanced-repeat-calibration
- blocked_by: m289-row16-aware-balanced-repeat-calibration
- supersedes: None
- invalidates: None

## Success Criteria

- fresh-seed row16-aware update preserves M183/M170 row16 and M267/M264 after interpolation
- candidate improves exact M270 beyond M287 weak repeat scale
- candidate passes full public replay protected-key and behavior gates before promotion
- actor input contract remains unchanged

## Failure Criteria

- safe alpha collapses back to near zero
- row16 passes but M267/M264 success drops are lost
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- repeat the row16-aware extra64 recipe on a fresh optimizer seed
- gate M183/M170 row16 and M267/M264 first
- run broader replay protected-key and behavior gates only if first gates pass with non-micro exact improvement

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M290
- do not change actor inputs
- do not skip row16 or M267/M264 first gates
- do not promote a near-zero interpolation artifact

## Failure Taxonomy

- none

## Scoreboard

- milestone: m290-row16-aware-balanced-repeat-fresh-seed
- type: driver_candidate
- checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844872
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m290x64_a500_and_admit_ppo_smoke
- reason: Fresh seed repeats row16-aware recipe with alpha 0.5 exact M270 delta -0.002097 and passes six replay surfaces protected key behavior gates; admit smoke-scale PPO only

## Next Blocker

m291-row16-aware-guarded-ppo-smoke
