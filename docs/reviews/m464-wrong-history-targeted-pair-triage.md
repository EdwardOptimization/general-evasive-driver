# m464-wrong-history-targeted-pair-triage Research Review

## Summary

- Generated at UTC: 20260523T210413Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: triage_pass_admit_m465_targeted_wrong_history_outcome_probe
- Decision reason: M464 exports 209 targeted pairs across 3 seeds 3 labels and 3 targets from the full M462 candidate pool

## Hypothesis

A targeted pair triage over the full M462 candidate-pair pool can build a more source-diverse wrong-history candidate surface than the generic matched_pairs compact output.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv, runs/m462_outcome_critical_selector_fresh_seed10200/wrong_history_audit.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m463-wrong-history-outcome-critical-redesign.json
- parent_objective: wrong-history targeted matched-current pair triage
- derived_from: m463-wrong-history-outcome-critical-redesign
- blocked_by: m463-wrong-history-outcome-critical-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- targeted pair triage CLI writes targeted_pairs.csv and summary.json
- targeted pairs >= 180 on M462 candidate pairs
- probe_seed_count >= 3
- obstacle_label_count >= 2
- target_count >= 3
- single_seed_share <= 0.50
- single_label_share <= 0.60
- no checkpoint is promoted

## Failure Criteria

- triage drops matched-current similarity constraints
- triage selects only one seed or one label
- triage requires privileged actor inputs
- triage treats high-margin-only rows as proof

## Evidence Gates

- implement targeted wrong-history pair triage from candidate_pairs.csv
- preserve matched-current similarity and target-z-delta constraints
- score pairs by hidden-vs-current separation and near-boundary proxies
- write targeted_pairs.csv and summary.json
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not use reset/zero-current rows as wrong-history proof
- do not select single-seed or single-label singleton surfaces

## Failure Taxonomy

- none

## Scoreboard

- milestone: m464-wrong-history-targeted-pair-triage
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: triage_pass_admit_m465_targeted_wrong_history_outcome_probe
- reason: M464 exports 209 targeted pairs across 3 seeds 3 labels and 3 targets from the full M462 candidate pool

## Next Blocker

m465-targeted-wrong-history-outcome-probe
