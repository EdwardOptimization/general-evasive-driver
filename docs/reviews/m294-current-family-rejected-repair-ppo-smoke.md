# m294-current-family-rejected-repair-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260522T200901Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_m294_repair_smoke_objective_regression_and_m267_washout
- Decision reason: M294 stronger anchor recovers one M267 row versus M291 raw but still loses rows 6 15 16 and every nonzero interpolation worsens exact M270

## Hypothesis

Stronger current-family rejected-history trajectory retention plus exact M270 gating can prevent the M291 PPO washout failure.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m292_m291_ppo_proof_washout_audit/failed_m267_m264_rows.csv
- parent_config: configs/ppo_m294_current_family_rejected_repair_smoke.json, experiments/manifests/m293-current-family-rejected-history-ppo-repair-design.json, docs/m293-current-family-rejected-history-ppo-repair-design.md
- parent_objective: smoke-scale PPO with stronger current-family rejected-history retention and exact M270 no-regression
- derived_from: m293-current-family-rejected-history-ppo-repair-design
- blocked_by: m293-current-family-rejected-history-ppo-repair-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw or interpolated M294 candidate is exact-M270 non-regressing versus m290x64_a500
- candidate preserves M183/M170 and M267/M264 first gates
- candidate passes full public replay protected-key and behavior gates before promotion
- candidate does not require near-zero interpolation
- actor input contract remains unchanged

## Failure Criteria

- raw and interpolated candidates worsen exact M270
- M267/M264 success drops are lost
- M183/M170 row16 is lost
- protected key or behavior gates fail
- PPO is run beyond smoke scale
- actor observation inputs change

## Evidence Gates

- run only smoke-scale PPO
- do not change actor inputs
- evaluate exact M270 no-regression first
- evaluate M183/M170 and M267/M264 first replay gates before broader gates
- run full replay protected-key and behavior gates only if first gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO in M294
- do not promote any candidate with exact M270 regression
- do not promote any candidate that loses M267/M264 success drops
- do not change actor observation inputs

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m294-current-family-rejected-repair-ppo-smoke
- type: driver_candidate
- checkpoint: runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m294_repair_smoke_objective_regression_and_m267_washout
- reason: M294 stronger anchor recovers one M267 row versus M291 raw but still loses rows 6 15 16 and every nonzero interpolation worsens exact M270

## Next Blocker

m295-current-family-ppo-repair-audit
