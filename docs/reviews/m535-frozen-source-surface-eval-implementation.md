# m535-frozen-source-surface-eval-implementation Research Review

## Summary

- Generated at UTC: 20260524T031243Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: frozen_source_surface_eval_implementation_pass_admit_m536_matrix_smoke
- Decision reason: M535 implements frozen source-surface evaluator validates L0 L2 L3 metadata and runs a 2-pair smoke with 0 invalid rows

## Hypothesis

A frozen source-surface evaluator can be implemented so trained L0, L2, and L3 baselines can be compared on matched natural source states rather than on divergent self-generated trajectories.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m532_matched_l0_short_train_seed3530/checkpoint.pt, runs/m532_matched_l2_short_train_seed3530/checkpoint.pt, runs/m532_matched_l3_short_train_seed3530/checkpoint.pt, runs/m533_matched_l0_short_train_seed3531/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt, runs/m533_matched_l0_short_train_seed3532/checkpoint.pt, runs/m533_matched_l2_short_train_seed3532/checkpoint.pt, runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json, runs/m524_natural_history_value_ablation/summary.json
- parent_config: experiments/manifests/m534-matched-history-natural-surface-eval-design.json
- parent_objective: frozen source-surface matched baseline evaluator
- derived_from: m534-matched-history-natural-surface-eval-design, m533-matched-short-train-repeat-seeds
- blocked_by: m534-matched-history-natural-surface-eval-design
- supersedes: None
- invalidates: None

## Success Criteria

- new evaluator loads and validates L0/L2/L3 checkpoints
- new evaluator can replay from a frozen source snapshot
- L3 target hidden is constructed from source observation history
- focused tests cover metadata validation and action-path dispatch
- research validation passes

## Failure Criteria

- evaluator only supports online recurrent checkpoints
- evaluator compares baselines on different source states
- checkpoint metadata mismatches are accepted silently
- checkpoint promotion is performed

## Evidence Gates

- implemented frozen source-surface evaluator for L0/L2/L3 checkpoints
- validated checkpoint level metadata before evaluation
- supported source M399 state reconstruction and target-policy replay
- wrote CSV and JSON smoke artifacts without checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not roll each baseline on its own trajectory and call states matched
- do not mix projected surfaces into natural claims
- do not promote checkpoint
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m535-frozen-source-surface-eval-implementation
- type: infrastructure
- checkpoint: runs/m535_frozen_source_surface_eval_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: frozen_source_surface_eval_implementation_pass_admit_m536_matrix_smoke
- reason: M535 implements frozen source-surface evaluator validates L0 L2 L3 metadata and runs a 2-pair smoke with 0 invalid rows

## Next Blocker

m536-frozen-source-natural-surface-matrix-smoke
