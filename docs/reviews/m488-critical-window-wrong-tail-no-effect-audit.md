# m488-critical-window-wrong-tail-no-effect-audit Research Review

## Summary

- Generated at UTC: 20260523T230157Z
- Type: gate
- Gate tier: process
- Promotion decision: wrong_tail_no_effect_audit_admit_m489_tail_action_sequence_amplification_design
- Decision reason: M488 shows wrong-tail first actions move but trajectory mean is 0.068 only 6.7 percent of reset and 14.9 percent of zero-current with 0 event rows so quick correction or non-outcome-aligned selection is the blocker

## Hypothesis

M487 failed because tail-aligned one-shot wrong histories create much smaller or more quickly corrected action/trajectory perturbations than reset and zero-current controls, and M486 target scores do not yet select outcome-sensitive wrong histories.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m487_critical_window_tail_aligned_outcome_summary/combined_summary.json, runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv, runs/m487_critical_window_tail_aligned_outcome_summary/variant_summary.csv
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m487-critical-window-tail-aligned-outcome-gate.json
- parent_objective: critical-window wrong-tail no-effect mechanism audit
- derived_from: m487-critical-window-tail-aligned-outcome-gate
- blocked_by: m487-critical-window-tail-aligned-outcome-gate
- supersedes: None
- invalidates: None

## Success Criteria

- produce row-level and aggregate audits for wrong_tail_once versus reset_tail and zero_current_tail
- report action distance, trajectory distance, margin gap, event rows, normal margin, config, label, target, and offset distributions
- identify the dominant no-effect mechanism
- pre-register the next milestone based on the audit result
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- audit cannot distinguish weak perturbation from selector mismatch or task insensitivity
- audit treats reset or zero-current controls as wrong-history proof
- audit proposes training before mechanism diagnosis
- actor contract changes

## Evidence Gates

- audit M487 wrong_tail_once action and trajectory distances against reset_tail and zero_current_tail controls
- compare proof-candidate and no-effect rows by config label target offset and normal margin
- test whether wrong_tail_once failures are explained by weak perturbation magnitude, quick recurrent correction, source selection, or non-outcome-aligned target score
- choose the next proof path before training or gate expansion
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not count reset or zero-current rows as wrong-history proof
- do not add privileged actor inputs
- do not select a new task before classifying the M487 no-effect mechanism

## Failure Taxonomy

- none

## Scoreboard

- milestone: m488-critical-window-wrong-tail-no-effect-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_tail_no_effect_audit_admit_m489_tail_action_sequence_amplification_design
- reason: M488 shows wrong-tail first actions move but trajectory mean is 0.068 only 6.7 percent of reset and 14.9 percent of zero-current with 0 event rows so quick correction or non-outcome-aligned selection is the blocker

## Next Blocker

m489-tail-action-sequence-amplification-design
