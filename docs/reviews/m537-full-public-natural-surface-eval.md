# m537-full-public-natural-surface-eval Research Review

## Summary

- Generated at UTC: 20260524T032623Z
- Type: gate
- Gate tier: proof
- Promotion decision: full_public_natural_eval_pass_admit_m538_paired_advantage_audit
- Decision reason: M537 full public natural matrix produced 20196 outcome rows; L3 leads L0/L2 on aggregate and every surface but no checkpoint is promoted

## Hypothesis

The frozen source evaluator can run the full public natural diagnostic matrix and reveal whether trained L3 or L2 baselines retain a natural-surface advantage beyond route smoke metrics.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m532_matched_l0_short_train_seed3530/checkpoint.pt, runs/m532_matched_l2_short_train_seed3530/checkpoint.pt, runs/m532_matched_l3_short_train_seed3530/checkpoint.pt, runs/m533_matched_l0_short_train_seed3531/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt, runs/m533_matched_l0_short_train_seed3532/checkpoint.pt, runs/m533_matched_l2_short_train_seed3532/checkpoint.pt, runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json
- parent_objective: full public frozen-source natural-surface eval
- derived_from: m536-frozen-source-natural-surface-matrix-smoke, m535-frozen-source-surface-eval-implementation
- blocked_by: m536-frozen-source-natural-surface-matrix-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- all four natural surface splits run or failures are diagnosed
- all nine checkpoint metadata validations pass
- aggregate all-row metrics are reported
- M526 event-subset overlay is reported separately
- research validation passes

## Failure Criteria

- full matrix cannot run on a baseline level
- invalid source snapshots dominate a surface
- M526 event rows are mixed into a private-holdout claim
- checkpoint promotion is performed

## Evidence Gates

- ran all nine matched checkpoints on four public natural surface splits
- preserved M497 and M487 provenance
- reported M526 event subset separately from all-row metrics
- did not promote checkpoint or claim private-holdout evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune checkpoints or configs from M536 output
- do not mix projected rows into natural claims
- do not promote checkpoint
- do not call public diagnostic rows private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m537-full-public-natural-surface-eval
- type: gate
- checkpoint: runs/m537_full_public_natural_surface_eval_aggregate/summary.json
- success_rate: 0.851901
- termination_rate: None
- clearance_margin_mean: 1.654668
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: full_public_natural_eval_pass_admit_m538_paired_advantage_audit
- reason: M537 full public natural matrix produced 20196 outcome rows; L3 leads L0/L2 on aggregate and every surface but no checkpoint is promoted

## Next Blocker

m538-natural-surface-paired-advantage-audit
