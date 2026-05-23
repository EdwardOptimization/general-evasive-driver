# m486-critical-window-targeted-pair-triage Research Review

## Summary

- Generated at UTC: 20260523T224848Z
- Type: gate
- Gate tier: proof
- Promotion decision: critical_window_targeted_triage_pass_admit_m487_tail_aligned_outcome_gate
- Decision reason: M486 exports 312 targeted pairs across 6 seeds 3 labels 3 targets with single-seed share 0.196 and near_threshold/late_high_energy split 157/155

## Hypothesis

The M485 critical-window matched-current surface is large enough to select a balanced targeted wrong-history pair surface for tail-aligned outcome proof gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m485_critical_window_matched_current_summary/combined_summary.json, runs/m485_critical_window_matched_current_summary/combined_matched_pairs.csv
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m485-critical-window-matched-current-mining.json
- parent_objective: source-diverse targeted wrong-history pair triage
- derived_from: m485-critical-window-matched-current-mining
- blocked_by: m485-critical-window-matched-current-mining
- supersedes: None
- invalidates: None

## Success Criteria

- targeted_pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- targeted surface is too small
- targeted surface is dominated by one seed label target or obstacle bucket
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run wrong_history_targeted_pair_triage on the combined M485 matched-current surface
- preserve source diversity across seeds labels targets and obstacle buckets
- export targeted pairs for tail-aligned wrong-history gate
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not skip targeted source-diversity caps
- do not run outcome/tail gates if triage surface is source-narrow

## Failure Taxonomy

- none

## Scoreboard

- milestone: m486-critical-window-targeted-pair-triage
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: critical_window_targeted_triage_pass_admit_m487_tail_aligned_outcome_gate
- reason: M486 exports 312 targeted pairs across 6 seeds 3 labels 3 targets with single-seed share 0.196 and near_threshold/late_high_energy split 157/155

## Next Blocker

m487-critical-window-tail-aligned-outcome-gate
