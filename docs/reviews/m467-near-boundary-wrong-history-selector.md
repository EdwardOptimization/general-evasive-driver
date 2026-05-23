# m467-near-boundary-wrong-history-selector Research Review

## Summary

- Generated at UTC: 20260523T211645Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: reject_wrong_history_gate_admit_m468_task_family_redesign
- Decision reason: M467 finds 35 near-boundary no-effect wrong-history rows 0 proof rows and 7 high-slack diagnostics so task-family redesign is next

## Hypothesis

A normal-margin-aware selector will show whether M465 contains any proof-quality wrong-history rows and will prevent high-slack margin-only rows from contaminating proof gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m465_targeted_wrong_history_selector/candidates.csv, runs/m465_targeted_wrong_history_selector/wrong_history_evidence_audit.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m466-near-boundary-wrong-history-redesign.json
- parent_objective: normal-margin-aware wrong-history proof selector
- derived_from: m466-near-boundary-wrong-history-redesign
- blocked_by: m466-near-boundary-wrong-history-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- selector CLI writes near_boundary_candidates proof_candidates near_boundary_no_effect high_slack_diagnostics and summary artifacts
- tests cover near-boundary proof acceptance and high-slack rejection
- M465 candidates can be classified without rerunning policy rollouts
- summary reports whether wrong-history proof expansion is admitted or rejected
- no checkpoint is promoted

## Failure Criteria

- selector accepts rows above the normal-margin ceiling as proof
- selector hides near-boundary no-effect rows
- selector requires privileged actor inputs
- actor contract changes

## Evidence Gates

- implement near-boundary wrong-history selector over existing candidate rows
- separate proof candidates from near-boundary no-effect and high-slack diagnostics
- write summary and CSV artifacts
- run selector on M465 candidates
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not count high-slack margin-only rows as proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m467-near-boundary-wrong-history-selector
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_wrong_history_gate_admit_m468_task_family_redesign
- reason: M467 finds 35 near-boundary no-effect wrong-history rows 0 proof rows and 7 high-slack diagnostics so task-family redesign is next

## Next Blocker

m468-near-boundary-task-family-redesign
