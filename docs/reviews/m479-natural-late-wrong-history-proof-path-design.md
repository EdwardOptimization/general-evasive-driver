# m479-natural-late-wrong-history-proof-path-design Research Review

## Summary

- Generated at UTC: 20260523T221545Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m480_late_once_wrong_history_implementation
- Decision reason: M479 designs late one-shot wrong-history variants to reduce artificial clamping before any deployable proof claim

## Hypothesis

Because clamped persistent wrong hidden is outcome-critical but one-shot wrong hidden is not, the least-artificial next test is a late one-shot wrong-history intervention at the critical decision window.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m478_persistent_wrong_history_intervention_gate/summary.json, runs/m478_persistent_wrong_history_intervention_gate/persistent_outcomes.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m478-persistent-wrong-history-intervention-implementation.json
- parent_objective: natural late wrong-history proof path design
- derived_from: m478-persistent-wrong-history-intervention-implementation
- blocked_by: m478-persistent-wrong-history-intervention-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- document why M478 is positive diagnostic evidence but not deployable proof
- define late one-shot variants such as wrong_late_4_once and wrong_late_8_once
- define whether implementation should extend M478 or create a separate gate
- define pass/fail criteria for natural-late evidence
- no checkpoint is promoted

## Failure Criteria

- design treats clamped hidden state as deployable proof
- design proposes training before late-one-shot evidence
- design changes actor inputs
- design relaxes proof thresholds

## Evidence Gates

- separate diagnostic clamped-hidden evidence from deployable self-ID evidence
- design late one-shot wrong-history variants without persistent clamping
- design pass/fail criteria comparing wrong_once, late_once, wrong_hold, reset, and zero-current
- pre-register the next implementation or task-design step
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not claim clamped hidden-state intervention as deployable proof
- do not add privileged actor inputs
- do not relax near-boundary proof thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m479-natural-late-wrong-history-proof-path-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m480_late_once_wrong_history_implementation
- reason: M479 designs late one-shot wrong-history variants to reduce artificial clamping before any deployable proof claim

## Next Blocker

m480-late-once-wrong-history-implementation
