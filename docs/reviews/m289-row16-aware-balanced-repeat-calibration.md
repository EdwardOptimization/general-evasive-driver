# m289-row16-aware-balanced-repeat-calibration Research Review

## Summary

- Generated at UTC: 20260522T194040Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m289x64_a600_public_gate_base
- Decision reason: M289 row16 extra64 alpha 0.6 improves exact M270 by 0.002778 and passes six replay surfaces protected key and behavior gates

## Hypothesis

A row16-aware lower-risk balanced recipe can reduce the M287 seed-fragile safe-alpha collapse while retaining the M267/M264 rejected-history direction.

## Lineage

- parent_checkpoint: runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt, runs/m287_balanced_rejected_trajectory_repeat/interpolation_refine/checkpoints/alpha_0_005.pt
- parent_dataset: runs/m288_balanced_repeat_seed_fragility_audit/fragile_row_action_margin_audit.csv, runs/m286_rejected_trajectory_anchor_balance_sweep/anchors/repeat2/combined_recovery_rejected_anchor.npz
- parent_config: experiments/manifests/m288-balanced-repeat-seed-fragility-audit.json, docs/m288-balanced-repeat-seed-fragility-audit.md
- parent_objective: row16-aware lower-risk balanced repeat before any PPO
- derived_from: m288-balanced-repeat-seed-fragility-audit
- blocked_by: m288-balanced-repeat-seed-fragility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- candidate preserves M183/M170 row16 positive terminal margin and M267/M264 success drops
- candidate improves exact M270 by more than M287 alpha 0.005 without requiring a near-zero alpha
- candidate passes broader public replay protected-key and behavior gates before promotion
- actor input contract remains unchanged

## Failure Criteria

- row16 still collapses before material objective improvement
- candidate preserves row16 but loses M267/M264 success drops
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- start from M272 or the registered M286 base as specified before execution
- calibrate a row16-aware lower-risk repeat recipe
- gate M183/M170 row16 and M267/M264 first
- run broader public gates only if row16 and M267/M264 pass with non-micro exact improvement

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M289
- do not change actor inputs
- do not ignore row16 terminal-margin slack
- do not promote a candidate that only passes by alpha near zero
- do not drop M267/M264 current-family retention

## Failure Taxonomy

- none

## Scoreboard

- milestone: m289-row16-aware-balanced-repeat-calibration
- type: driver_candidate
- checkpoint: runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844999
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m289x64_a600_public_gate_base
- reason: M289 row16 extra64 alpha 0.6 improves exact M270 by 0.002778 and passes six replay surfaces protected key and behavior gates

## Next Blocker

m290-row16-aware-balanced-repeat-fresh-seed
