# m371-alpha06-old-key-gap-p10-audit Research Review

## Summary

- Generated at UTC: 20260523T121627Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m372_old_key_gap_distribution_retention_design
- Decision reason: M371 classifies alpha 0.6 as old-key gap-distribution erosion without accepted regressions; five compact rows drive gap p10 below threshold and thresholds remain unchanged

## Hypothesis

The alpha 0.6 old-key failure may be a gap-distribution erosion without accepted regressions; auditing the responsible rows should determine whether the next repair needs gap-distribution retention rather than more hard-row endpoint pressure.

## Lineage

- parent_checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt, runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
- parent_dataset: runs/m369_hard_row_interpolation_old_key_targeted_replay/guard_results.csv, runs/m369_hard_row_interp_a600_old_key_replay_gate/summary.json, docs/m370-full-public-gate-for-m369-a400.md
- parent_config: experiments/manifests/m370-full-public-gate-for-m369-a400.json
- parent_objective: audit the first tested alpha 0.6 old-key compact gap-p10 failure before more repair or PPO
- derived_from: m370-full-public-gate-for-m369-a400
- blocked_by: m370-full-public-gate-for-m369-a400
- supersedes: None
- invalidates: None

## Success Criteria

- audit identifies the rows responsible for alpha 0.6 gap-p10 failure
- audit compares alpha 0.4 and alpha 0.6 deltas
- audit recommends gap-distribution retention, another hard-row overlay, or stopping this branch
- research validation passes

## Failure Criteria

- audit ignores alpha 0.6 gap-p10 failure
- audit changes acceptance thresholds to pass alpha 0.6
- actor input contract changes
- research validation fails

## Evidence Gates

- audit only; no PPO run
- identify alpha 0.6 worst gap-p10 rows
- compare alpha 0.4 and alpha 0.6 compact old-key deltas
- classify whether failure is broad gap erosion, local normal-margin erosion, or metric artifact
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote alpha 0.6
- do not lower old-key gap-p10 threshold
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m371-alpha06-old-key-gap-p10-audit
- type: gate
- checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m372_old_key_gap_distribution_retention_design
- reason: M371 classifies alpha 0.6 as old-key gap-distribution erosion without accepted regressions; five compact rows drive gap p10 below threshold and thresholds remain unchanged

## Next Blocker

m372-old-key-gap-distribution-retention-design
