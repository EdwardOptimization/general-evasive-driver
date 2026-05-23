# m480-late-once-wrong-history-implementation Research Review

## Summary

- Generated at UTC: 20260523T222249Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: late_once_margin_only_source_narrow_admit_m481_critical_window_design
- Decision reason: M480 late one-shot variants yield 16 margin-only proof-style rows but 0 event rows and only 2 probe seeds while clamped wrong_hold_16 remains diagnostic with 25 proof rows

## Hypothesis

If timing is the key blocker, a late one-shot wrong-history injection will create proof-style degradation without clamping hidden state across multiple steps.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m478_persistent_wrong_history_intervention_gate/summary.json, runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m479-natural-late-wrong-history-proof-path-design.json
- parent_objective: late one-shot wrong-history diagnostic implementation
- derived_from: m479-natural-late-wrong-history-proof-path-design
- blocked_by: m479-natural-late-wrong-history-proof-path-design
- supersedes: None
- invalidates: None

## Success Criteria

- late-one-shot variants are implemented with tested semantics
- smoke run completes on M474 adversarial pairs
- wrong_late_*_once proof counts are reported separately
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- late-one-shot semantics are ambiguous or untested
- implementation changes actor inputs
- smoke run fails
- training or checkpoint promotion is performed

## Evidence Gates

- add wrong_late_2_once wrong_late_4_once wrong_late_8_once and wrong_late_12_once variants
- add focused tests for late-one-shot semantics
- rerun the persistent wrong-history diagnostic gate on M474 adversarial pairs
- report late-one-shot proof counts separately from clamped hold counts
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim intervention evidence as deployable proof
- do not count clamped hold rows as late-one-shot proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m480-late-once-wrong-history-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: late_once_margin_only_source_narrow_admit_m481_critical_window_design
- reason: M480 late one-shot variants yield 16 margin-only proof-style rows but 0 event rows and only 2 probe seeds while clamped wrong_hold_16 remains diagnostic with 25 proof rows

## Next Blocker

m481-critical-window-history-necessity-design
