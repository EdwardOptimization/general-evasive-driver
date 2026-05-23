# m405-recovery-aware-exact-projection-design Research Review

## Summary

- Generated at UTC: 20260523T154650Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m406_recovery_aware_exact_projection_probe
- Decision reason: M405 designs lexicographic recovery-aware exact projection: exact M297/M270/old-key feasibility first and recovery movement only as secondary merit

## Hypothesis

Because recovery-heavy movement conflicts broadly with exact M297/M270, the next repair should be a recovery-aware exact projection design rather than another scalar weight sweep.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m404_recovery_exact_conflict_row_audit/m297_row_deltas.csv, runs/m404_recovery_exact_conflict_row_audit/m270_row_deltas.csv, runs/m403_lrec1e10_interpolation_old_key_targeted_replay/guard_results.csv, runs/m403_r1e10a600_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m404-recovery-exact-conflict-row-audit.json
- parent_objective: design recovery-aware exact projection after broad exact-anchor conflict
- derived_from: m404-recovery-exact-conflict-row-audit
- blocked_by: m404-recovery-exact-conflict-row-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define a projection objective that treats exact M297/M270 no-regression as hard feasibility
- define recovery-target action movement as a secondary merit or tie-breaker
- define how M267/M264 and old-key replay remain outer gates
- pre-register the implementation or probe milestone

## Failure Criteria

- design lowers exact or replay thresholds
- design changes actor inputs or output contract
- research validation fails

## Evidence Gates

- no PPO run
- design only
- preserve exact M297/M270 as hard feasibility objectives
- use recovery movement only as secondary merit objective
- retain old-key replay and M267/M264 as outer proof gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m405-recovery-aware-exact-projection-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m406_recovery_aware_exact_projection_probe
- reason: M405 designs lexicographic recovery-aware exact projection: exact M297/M270/old-key feasibility first and recovery movement only as secondary merit

## Next Blocker

m406-recovery-aware-exact-projection-probe
