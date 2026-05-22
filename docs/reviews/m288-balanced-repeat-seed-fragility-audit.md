# m288-balanced-repeat-seed-fragility-audit Research Review

## Summary

- Generated at UTC: 20260522T193252Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_row16_aware_balanced_repeat
- Decision reason: M288 finds M287 seed fragility comes from old M183/M170 row16 terminal-margin cliff while M267/M264 remains intact

## Hypothesis

The M287 safe-alpha collapse is caused by seed-sensitive drift on old M183/M170 fragile rows rather than loss of the M267/M264 current-family rejected-history direction.

## Lineage

- parent_checkpoint: runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt, runs/m287_balanced_rejected_trajectory_repeat/interpolation_refine/checkpoints/alpha_0_005.pt
- parent_dataset: runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/alpha_summary.csv, runs/m287_balanced_rejected_trajectory_repeat/interpolation_refine/alpha_summary.csv
- parent_config: experiments/manifests/m286-rejected-trajectory-anchor-balance-sweep.json, experiments/manifests/m287-balanced-rejected-trajectory-repeat.json
- parent_objective: audit why the M286 repeat2 recipe has a wide safe alpha on seed10079 and a collapsed safe alpha on seed10080
- derived_from: m287-balanced-rejected-trajectory-repeat
- blocked_by: m287-balanced-rejected-trajectory-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- identify the M183/M170 rows responsible for the M286 versus M287 safe-alpha difference
- quantify action drift or margin drift on those rows
- separate current-family retention success from old-surface normal-success fragility
- pre-register one next repair recipe before any further update or PPO

## Failure Criteria

- audit cannot explain why M287 safe alpha collapses
- audit recommends PPO without a repeat-safe proof-retention recipe
- actor observation inputs change

## Evidence Gates

- audit only; do not run PPO
- compare M286 and M287 raw and selected interpolation candidates
- identify which M183/M170 rows create the seed-fragile safe-alpha collapse
- compare first-action and trajectory action drift on failed old-surface rows
- recommend exactly one next repair recipe

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M288
- do not promote a checkpoint in M288
- do not change actor inputs
- do not ignore M183/M170 row-level failure evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m288-balanced-repeat-seed-fragility-audit
- type: gate
- checkpoint: runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844084
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: repair_with_row16_aware_balanced_repeat
- reason: M288 finds M287 seed fragility comes from old M183/M170 row16 terminal-margin cliff while M267/M264 remains intact

## Next Blocker

m289-row16-aware-balanced-repeat-calibration
