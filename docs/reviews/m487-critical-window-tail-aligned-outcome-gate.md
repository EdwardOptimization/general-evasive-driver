# m487-critical-window-tail-aligned-outcome-gate Research Review

## Summary

- Generated at UTC: 20260523T225638Z
- Type: gate
- Gate tier: proof
- Promotion decision: critical_window_tail_gate_reject_wrong_tail_proof_admit_m488_no_effect_audit
- Decision reason: M487 wrong_tail_once has 11 proof rows and 0 event rows with single-label share 0.909 while reset/zero-current controls have 333 proof rows and 41 events so natural tail proof is rejected and no checkpoint is promoted

## Hypothesis

The M486 source-diverse critical-window targeted pairs will make tail-aligned one-shot wrong-history interventions produce source-diverse event or margin proof beyond the single-pair M482 signal.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m486_critical_window_targeted_pair_triage/summary.json, runs/m486_critical_window_targeted_pair_triage/targeted_pairs.csv
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m486-critical-window-targeted-pair-triage.json
- parent_objective: tail-aligned wrong-history outcome gate on critical-window targeted pairs
- derived_from: m486-critical-window-targeted-pair-triage
- blocked_by: m486-critical-window-targeted-pair-triage
- supersedes: None
- invalidates: None

## Success Criteria

- tail-aligned gates run on both critical configs without sampling or snapshot failure
- wrong_tail_once proof_candidate_count >= 16
- wrong_tail_once event rows >= 4
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- wrong_tail_once rows remain source-narrow
- only reset or zero-current controls show outcome degradation
- tail split is invalid or drops most targeted pairs
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- split M486 targeted pairs by critical_config
- run tail_aligned_wrong_history_gate on each split with the matching env config
- combine wrong_tail_once proof and event rows across splits
- keep reset and zero-current controls separate from wrong-tail proof
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count reset or zero-current rows as wrong-tail proof
- do not count clamped hidden-state interventions as natural proof
- do not relax source-diversity thresholds after seeing outcomes

## Failure Taxonomy

- none

## Scoreboard

- milestone: m487-critical-window-tail-aligned-outcome-gate
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: critical_window_tail_gate_reject_wrong_tail_proof_admit_m488_no_effect_audit
- reason: M487 wrong_tail_once has 11 proof rows and 0 event rows with single-label share 0.909 while reset/zero-current controls have 333 proof rows and 41 events so natural tail proof is rejected and no checkpoint is promoted

## Next Blocker

m488-critical-window-wrong-tail-no-effect-audit
