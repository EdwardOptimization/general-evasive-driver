# m482-tail-aligned-wrong-history-gate-implementation Research Review

## Summary

- Generated at UTC: 20260523T223215Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: tail_aligned_event_signal_source_narrow_admit_m483_critical_window_config_design
- Decision reason: M482 tail-aligned one-shot swaps produce 14 proof-style rows and 3 event rows but all events come from one source pair so the natural proof gate fails

## Hypothesis

If M480 late-one-shot evidence was weakened by stale right hidden state, then tail-aligned wrong-history swaps at left_step+S/right_step+S will produce stronger source-diverse one-shot outcome degradation without hidden-state clamping.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m480_late_once_wrong_history_intervention_gate/late_once_summary.json, runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m481-critical-window-history-necessity-design.json
- parent_objective: tail-aligned one-shot wrong-history diagnostic implementation
- derived_from: m481-critical-window-history-necessity-design
- blocked_by: m481-critical-window-history-necessity-design
- supersedes: None
- invalidates: None

## Success Criteria

- tail-aligned snapshots are collected for offsets 4 8 12 and 16
- valid tail-pair counts are reported per offset
- one-shot wrong-tail outcomes are reported separately from held diagnostics
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- tail alignment semantics are ambiguous or untested
- implementation changes actor inputs
- invalid tail pairs are silently counted as failures or successes
- training or checkpoint promotion is performed

## Evidence Gates

- collect left and right snapshots at matched tail offsets
- run one-shot wrong-tail hidden intervention without hidden-state clamping
- compare offsets 4 8 12 and 16 against reset and zero-current controls
- report one-shot rows separately from any held diagnostic rows
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count clamped rows as natural proof
- do not relax source-diversity thresholds
- do not hide invalid tail pairs that terminate before the requested offset

## Failure Taxonomy

- none

## Scoreboard

- milestone: m482-tail-aligned-wrong-history-gate-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: tail_aligned_event_signal_source_narrow_admit_m483_critical_window_config_design
- reason: M482 tail-aligned one-shot swaps produce 14 proof-style rows and 3 event rows but all events come from one source pair so the natural proof gate fails

## Next Blocker

m483-critical-window-config-design
