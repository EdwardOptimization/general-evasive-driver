# m769-v4-limited-residual-holdout-replay-design Research Review

## Summary

- Generated at UTC: 20260525T005115Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: limited_residual_holdout_replay_design_admit_m770
- Decision reason: M769 designs limited no-PPO residual replay on sparse fresh M767 corpus with alpha 0.2 primary and diagnostic alphas 0.5 1.0

## Hypothesis

A limited no-PPO residual replay can test whether M761's closed-loop mechanism signal transfers to the fresh but sparse M767 holdout corpus.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m768-v4-fresh-source-holdout-wave-audit.md, runs/m767_v4_source_holdout_corpus_export/summary.json, runs/m767_v4_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m767_v4_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m768-v4-fresh-source-holdout-wave-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design limited no-PPO residual replay on fresh M767 holdout corpus
- derived_from: m768-v4-fresh-source-holdout-wave-audit
- blocked_by: m768-v4-fresh-source-holdout-wave-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M769 defines input corpus and alphas
- M769 defines limited-holdout claim scope
- M769 defines normal retention and intervention sensitivity gates
- M769 blocks training PPO and promotion
- M769 admits only implementation as next step

## Failure Criteria

- design treats M767 as clean broad holdout
- design admits residual retraining
- design admits PPO or promotion
- design hides source sparsity
- design lacks alpha-specific reporting

## Evidence Gates

- M769 designs limited residual holdout replay on M767 corpus
- M769 labels source-holdout evidence as limited and sparse
- M769 prioritizes alpha 0.2 with alpha 0.5 and 1.0 diagnostic
- M769 keeps no-PPO no-promotion scope
- M769 preserves normal retention and intervention sensitivity metrics

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not tune alpha from holdout results
- do not call limited holdout evidence a promotion gate
- do not run PPO
- do not promote a checkpoint
- do not hide sparse-source caveats

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m769-v4-limited-residual-holdout-replay-design
- type: infrastructure
- checkpoint: docs/m769-v4-limited-residual-holdout-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: limited_residual_holdout_replay_design_admit_m770
- reason: M769 designs limited no-PPO residual replay on sparse fresh M767 corpus with alpha 0.2 primary and diagnostic alphas 0.5 1.0

## Next Blocker

m770-v4-limited-residual-holdout-replay-implementation
