# m498-natural-belief-wrong-history-no-effect-audit Research Review

## Summary

- Generated at UTC: 20260523T235354Z
- Type: gate
- Gate tier: proof
- Promotion decision: audit_wrong_history_weak_or_margin_only_admit_m499_action_sensitive_selector_design
- Decision reason: M498 finds wrong-history trajectory mean is 0.055 versus reset 1.006 and zero-current 0.451 so one-shot wrong-history corrects quickly and target-z triage should be replaced by action-sensitive selection

## Hypothesis

M497 rejected wrong-history event proof because the one-shot wrong-history branch remains too weak or not outcome-aligned relative to reset/zero-current controls, not because the natural decision-window rows are insensitive.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_summary/combined_summary.json, runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m497-natural-belief-decision-window-outcome-gate.json
- parent_objective: natural decision-window wrong-history no-effect audit
- derived_from: m497-natural-belief-decision-window-outcome-gate
- blocked_by: m497-natural-belief-decision-window-outcome-gate
- supersedes: None
- invalidates: None

## Success Criteria

- report wrong-history action and trajectory distance distributions
- report reset and zero-current control distance distributions
- report proof and event rows by config label target offset and seed
- classify the next blocker and next admissible step
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- M497 artifacts are insufficient for audit
- audit cannot separate wrong-history no-effect from control sensitivity
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- audit M497 wrong-history action and trajectory distances against reset and zero-current controls
- compare proof-candidate and no-effect rows by config label target offset and normal margin
- classify whether the blocker is weak wrong-history perturbation, source concentration, target-score misalignment, or task/intervention mismatch
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m498-natural-belief-wrong-history-no-effect-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: audit_wrong_history_weak_or_margin_only_admit_m499_action_sensitive_selector_design
- reason: M498 finds wrong-history trajectory mean is 0.055 versus reset 1.006 and zero-current 0.451 so one-shot wrong-history corrects quickly and target-z triage should be replaced by action-sensitive selection

## Next Blocker

pending M498 natural belief wrong-history no-effect audit
