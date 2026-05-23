# m461-outcome-critical-matched-current-selector-implementation Research Review

## Summary

- Generated at UTC: 20260523T204921Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: selector_pass_admit_m462_fresh_repeat_wrong_history_audit
- Decision reason: M461 selector selects 20 compact reset/zero-current outcome-critical rows but no wrong-history or success-drop rows so fresh repeat audit is next

## Hypothesis

Implementing outcome-critical selection will distinguish true matched-current self-ID candidates from M459's action-only surface and decide whether the M457 task family should continue.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv, runs/m459_late_reveal_matched_history_action_gate/action_interventions.csv, runs/m459_late_reveal_matched_history_outcome_gate/outcome_interventions.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m460-outcome-critical-matched-current-selector-design.json
- parent_objective: outcome-critical matched-current selector implementation
- derived_from: m460-outcome-critical-matched-current-selector-design
- blocked_by: m460-outcome-critical-matched-current-selector-design
- supersedes: None
- invalidates: None

## Success Criteria

- selector CLI writes candidates compact corpus and summary JSON
- tests cover success-drop margin-gap action-only rejection and diversity caps
- M459 pairs can be processed without sampling failure
- documentation reports accepted outcome-critical rows or structured rejection
- no checkpoint is promoted

## Failure Criteria

- selector accepts action-only rows as outcome-critical
- selector ignores matched-current similarity fields
- selector cannot process M459 artifacts
- actor contract changes

## Evidence Gates

- implement an outcome-critical matched-current selector
- reject action-only rows unless they also have continuation outcome degradation
- write candidate compact and summary artifacts
- add focused selector tests
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not treat action-distance-only rows as outcome-critical

## Failure Taxonomy

- none

## Scoreboard

- milestone: m461-outcome-critical-matched-current-selector-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: selector_pass_admit_m462_fresh_repeat_wrong_history_audit
- reason: M461 selector selects 20 compact reset/zero-current outcome-critical rows but no wrong-history or success-drop rows so fresh repeat audit is next

## Next Blocker

m462-outcome-critical-selector-repeat-audit
