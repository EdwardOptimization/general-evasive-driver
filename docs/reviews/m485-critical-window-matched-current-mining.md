# m485-critical-window-matched-current-mining Research Review

## Summary

- Generated at UTC: 20260523T224601Z
- Type: gate
- Gate tier: proof
- Promotion decision: critical_window_matched_surface_pass_admit_m486_targeted_wrong_history_triage
- Decision reason: M485 combined matched-current surface has 5802 accepted pairs across 6 seeds 3 labels 3 targets with single-seed share 0.178 and single-label share 0.547

## Hypothesis

The M484 critical-window configs are robust enough to support source-diverse matched-current ambiguity mining before tail-aligned wrong-history proof gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m484_critical_window_config_validation/sampling_summary.json, runs/m484_critical_window_config_validation/behavior_summary.json
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m484-critical-window-config-implementation.json
- parent_objective: critical-window matched-current mining before tail-aligned proof gates
- derived_from: m484-critical-window-config-implementation
- blocked_by: m484-critical-window-config-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- matched-current mining completes on both configs without sampling failure
- combined accepted_pair_count >= 512
- combined probe_seed_count >= 6
- combined obstacle_label_count >= 2
- combined target_count >= 2
- combined single_seed_share <= 0.50
- combined single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- either config cannot produce enough matched-current candidates
- candidate surface is source-narrow
- only one obstacle label or target dominates
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run matched-current mining on both M484 critical-window configs
- require source-diverse candidate surfaces before wrong-history proof gates
- report accepted pairs, physical pairs, labels, targets, visible distance, and target z delta
- do not train or promote checkpoint
- do not run private holdout tuning

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not skip source-diversity checks before tail-aligned gates
- do not count aggregate behavior smoke as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m485-critical-window-matched-current-mining
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: critical_window_matched_surface_pass_admit_m486_targeted_wrong_history_triage
- reason: M485 combined matched-current surface has 5802 accepted pairs across 6 seeds 3 labels 3 targets with single-seed share 0.178 and single-label share 0.547

## Next Blocker

m486-critical-window-targeted-pair-triage
