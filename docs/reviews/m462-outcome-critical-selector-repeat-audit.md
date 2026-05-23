# m462-outcome-critical-selector-repeat-audit Research Review

## Summary

- Generated at UTC: 20260523T205609Z
- Type: gate
- Gate tier: generalization
- Promotion decision: fresh_repeat_pass_wrong_history_weak_admit_m463
- Decision reason: M462 fresh repeat selects 34 compact rows with success/collision evidence for reset/zero-current but wrong-history has zero compact rows and only 8 raw source-narrow accepted rows

## Hypothesis

M461's selector can find outcome-critical reset/zero-current rows, but fresh repeat is needed to test robustness and determine whether wrong-history belief evidence exists.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m461_outcome_critical_selector_m459_pairs/compact_corpus.csv, runs/m461_outcome_critical_selector_m459_pairs/summary.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m461-outcome-critical-matched-current-selector-implementation.json
- parent_objective: fresh repeat and wrong-history coverage audit for outcome-critical selector
- derived_from: m461-outcome-critical-matched-current-selector-implementation
- blocked_by: m461-outcome-critical-matched-current-selector-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- fresh repeat completes without scenario sampling failure
- selector outputs compact corpus or structured rejection
- wrong-history coverage is reported explicitly
- success-drop and margin-gap evidence are reported separately
- no checkpoint is promoted

## Failure Criteria

- repeat only reuses M459 rows
- wrong-history absence is hidden in aggregate counts
- margin-gap-only evidence is treated as success proof
- actor contract changes

## Evidence Gates

- repeat outcome-critical selector on fresh source-diverse matched-current artifacts
- audit whether wrong-history or delayed-history rows become outcome-critical
- separate margin-gap-only evidence from success-drop evidence
- decide between wrong-history gate expansion and task-family redesign
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not claim wrong-history proof from reset/zero-current rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m462-outcome-critical-selector-repeat-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fresh_repeat_pass_wrong_history_weak_admit_m463
- reason: M462 fresh repeat selects 34 compact rows with success/collision evidence for reset/zero-current but wrong-history has zero compact rows and only 8 raw source-narrow accepted rows

## Next Blocker

m463-wrong-history-outcome-critical-redesign
