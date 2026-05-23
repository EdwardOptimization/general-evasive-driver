# m367-old-key-hard-row-weighting-design Research Review

## Summary

- Generated at UTC: 20260523T115211Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m368_old_key_hard_row_feedback_implementation
- Decision reason: M367 designs hard-row overlay and wrong-branch weighting feedback for the alpha 0.2 old-key sign-crossing row without changing actor inputs or thresholds

## Hypothesis

Old-key alpha 0.2 fails because one wrong-history branch crosses the terminal margin sign; feeding that replay regression back as a hard-row weight or constraint may allow larger safe old-key-aware repair steps.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt, runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: docs/m366-alpha02-old-key-regression-audit.md, runs/m364_old_key_aware_repair_alpha02_old_key_replay_gate/old_key_replay_comparison_rows.csv
- parent_config: experiments/manifests/m366-alpha02-old-key-regression-audit.json
- parent_objective: design hard-row feedback from old-key replay regressions into old-key repair corpus weights
- derived_from: m366-alpha02-old-key-regression-audit
- blocked_by: m366-alpha02-old-key-regression-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies hard-row metadata schema
- design states how hard-row weights affect old-key preference and rejected-action anchor terms
- design registers an implementation or probe milestone
- research validation passes

## Failure Criteria

- design lowers closed-loop old-key gate thresholds
- design ignores wrong-history margin sign crossing
- actor input contract changes
- research validation fails

## Evidence Gates

- design only; no PPO run
- do not promote alpha 0.2
- preserve old-key replay as authoritative gate
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower old-key acceptance thresholds
- do not use hidden vehicle parameters as actor inputs
- do not run PPO
- do not treat local surrogate pass as closed-loop proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m367-old-key-hard-row-weighting-design
- type: infrastructure
- checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m368_old_key_hard_row_feedback_implementation
- reason: M367 designs hard-row overlay and wrong-branch weighting feedback for the alpha 0.2 old-key sign-crossing row without changing actor inputs or thresholds

## Next Blocker

m368-old-key-hard-row-feedback-implementation
