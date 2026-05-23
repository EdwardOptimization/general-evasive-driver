# m476-wrong-history-no-effect-mechanism-audit Research Review

## Summary

- Generated at UTC: 20260523T220218Z
- Type: gate
- Gate tier: proof
- Promotion decision: wrong_history_no_effect_audit_admit_m477_persistent_intervention_design
- Decision reason: M476 diagnoses wrong-history trajectory perturbation as too weak or quickly corrected: mean trajectory distance 0.045794 vs reset 0.883482 and zero-current 0.395153

## Hypothesis

M475 failed because wrong matched-history injections change first action but do not persist long enough or target terminal-sensitive directions strongly enough to change closed-loop outcome.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m475_combined_adversarial_action_gate/action_interventions.csv, runs/m475_combined_adversarial_outcome_gate/outcome_interventions.csv, runs/m475_combined_adversarial_outcome_selector/candidates.csv, runs/m475_combined_adversarial_near_boundary_selector/wrong_history_classified.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m475-combined-adversarial-outcome-proof-probe.json
- parent_objective: wrong-history no-effect mechanism audit
- derived_from: m475-combined-adversarial-outcome-proof-probe
- blocked_by: m475-combined-adversarial-outcome-proof-probe
- supersedes: None
- invalidates: None

## Success Criteria

- produce a row-level audit of wrong-history action distance, right-action closeness, terminal margin gap, return gap, and outcome-critical status
- compare wrong-history against reset and zero-current rows on the same targets and labels
- identify the dominant no-effect mechanism
- choose the next path from persistent-history intervention, shorter-emergency task design, or stronger outcome-sensitive adversarial scoring
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- audit cannot explain why wrong-history rows are no-effect
- audit treats reset/zero-current degradation as wrong-history proof
- audit proposes training before mechanism diagnosis
- actor contract changes

## Evidence Gates

- audit wrong-history action distance versus outcome margin gap
- compare wrong-history rows with reset/zero-current degradation rows on the same surface
- identify whether the no-effect blocker is action weakness, fast recurrent correction, terminal slack, or selector metric mismatch
- pre-register the next repair path
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not count reset/zero-current degradation as wrong-history proof
- do not count high-slack diagnostics as proof
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m476-wrong-history-no-effect-mechanism-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_no_effect_audit_admit_m477_persistent_intervention_design
- reason: M476 diagnoses wrong-history trajectory perturbation as too weak or quickly corrected: mean trajectory distance 0.045794 vs reset 0.883482 and zero-current 0.395153

## Next Blocker

m477-persistent-wrong-history-intervention-design
