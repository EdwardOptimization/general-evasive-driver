# m536-frozen-source-natural-surface-matrix-smoke Research Review

## Summary

- Generated at UTC: 20260524T031635Z
- Type: gate
- Gate tier: process
- Promotion decision: matrix_smoke_pass_admit_m537_full_public_natural_eval
- Decision reason: M536 runs all nine matched checkpoints on small short-reveal and warmup natural subsets; one source-tail miss is diagnosed and no final ranking is claimed

## Hypothesis

The frozen source-surface evaluator can scale from the M535 3-checkpoint smoke to the full nine-checkpoint matched baseline matrix on small natural surface subsets.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m532_matched_l0_short_train_seed3530/checkpoint.pt, runs/m532_matched_l2_short_train_seed3530/checkpoint.pt, runs/m532_matched_l3_short_train_seed3530/checkpoint.pt, runs/m533_matched_l0_short_train_seed3531/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt, runs/m533_matched_l0_short_train_seed3532/checkpoint.pt, runs/m533_matched_l2_short_train_seed3532/checkpoint.pt, runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json
- parent_objective: frozen source natural-surface matrix smoke
- derived_from: m535-frozen-source-surface-eval-implementation, m534-matched-history-natural-surface-eval-design
- blocked_by: m535-frozen-source-surface-eval-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- all nine checkpoints are evaluated on both small natural surface subsets
- metadata validation passes for all checkpoints
- invalid rows are zero or diagnosed
- summary artifacts are written
- research validation passes

## Failure Criteria

- any baseline level cannot be evaluated
- metadata mismatch is accepted silently
- invalid source snapshots dominate the smoke
- checkpoint promotion is performed

## Evidence Gates

- ran frozen source evaluator on all nine matched short-train checkpoints
- covered short-reveal and warmup natural surfaces with small max_pairs
- verified metadata and diagnosed invalid-row counts
- no checkpoint promotion or final ranking claimed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune checkpoints or configs from smoke output
- do not mix projected rows into natural claims
- do not promote checkpoint
- do not call smoke metrics paper-level evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m536-frozen-source-natural-surface-matrix-smoke
- type: gate
- checkpoint: runs/m536_frozen_source_matrix_smoke_warmup_capability/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: matrix_smoke_pass_admit_m537_full_public_natural_eval
- reason: M536 runs all nine matched checkpoints on small short-reveal and warmup natural subsets; one source-tail miss is diagnosed and no final ranking is claimed

## Next Blocker

m537-full-public-natural-surface-eval
