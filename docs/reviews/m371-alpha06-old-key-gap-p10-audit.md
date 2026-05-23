# m371-alpha06-old-key-gap-p10-audit Research Review

## Summary

- Generated at UTC: 20260523T121345Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M371 completes by classifying the alpha 0.6 old-key gap-p10 failure and registering the next blocker without training or threshold changes.

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

- No scoreboard row recorded.

## Next Blocker

pending M371 alpha 0.6 old-key gap-p10 audit
