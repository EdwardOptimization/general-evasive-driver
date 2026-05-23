# m404-recovery-exact-conflict-row-audit Research Review

## Summary

- Generated at UTC: 20260523T154231Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m405_recovery_aware_exact_projection_design
- Decision reason: M404 finds broad exact-anchor conflict: 17/17 M297 rows and 99/99 M270 rows regress under recovery-heavy alpha 0.025

## Hypothesis

The recovery-heavy direction is blocked by specific exact M297/M270 rows rather than by old-key compact replay itself, so row-level attribution should reveal the active conflict set.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m403_r1e10a025_exact_eval/summary.json, runs/m403_r1e10a050_exact_eval/summary.json, runs/m403_r1e10a100_exact_eval/summary.json, runs/m403_lrec1e10_interpolation_old_key_targeted_replay/guard_results.csv, runs/m403_r1e10a600_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m403-old-key-normal-recovery-weight-sweep.json
- parent_objective: attribute exact M297/M270 row conflicts against old-key normal recovery direction
- derived_from: m403-old-key-normal-recovery-weight-sweep
- blocked_by: m403-old-key-normal-recovery-weight-sweep
- supersedes: None
- invalidates: None

## Success Criteria

- compute per-row M297 and M270 loss deltas for recovery-heavy alpha candidates
- rank rows by positive regression contribution
- classify whether the conflict is sparse or broad
- pre-register the next repair or redesign milestone

## Failure Criteria

- per-row exact losses cannot be reproduced
- audit changes actor inputs or thresholds
- research validation fails

## Evidence Gates

- no PPO run
- attribute per-row exact M297/M270 loss changes under the recovery-heavy direction
- identify whether conflicts are concentrated in a few rows or broad across the exact corpora
- decide whether next task is row reweighting, corpus refresh, trajectory residual design, or stop this direction

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m404-recovery-exact-conflict-row-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m405_recovery_aware_exact_projection_design
- reason: M404 finds broad exact-anchor conflict: 17/17 M297 rows and 99/99 M270 rows regress under recovery-heavy alpha 0.025

## Next Blocker

m405-recovery-aware-exact-projection-design
