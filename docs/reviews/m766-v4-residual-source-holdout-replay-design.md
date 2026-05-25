# m766-v4-residual-source-holdout-replay-design Research Review

## Summary

- Generated at UTC: 20260525T003546Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_fresh_source_holdout_wave_design_admit_m767
- Decision reason: M766 finds no clean extra M752/M755 positive holdout and designs disjoint-seed fresh source-holdout wave before residual replay

## Hypothesis

A fresh source-holdout replay can be designed to test whether the M761 residual closed-loop signal generalizes beyond the public M755/M761 corpus.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m765-v4-residual-closed-loop-replay-audit.md, runs/m764_v4_residual_closed_loop_replay/summary.json, runs/m764_v4_residual_closed_loop_replay/alpha_metrics.csv, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m749_extreme_fault_distribution_v4/summary.json
- parent_config: experiments/manifests/m765-v4-residual-closed-loop-replay-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design fresh source-holdout replay for M761 residual head
- derived_from: m765-v4-residual-closed-loop-replay-audit
- blocked_by: m765-v4-residual-closed-loop-replay-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M766 defines what counts as fresh relative to M761
- M766 defines source selection and fallback source-mining plan
- M766 defines alpha set and conservative primary alpha
- M766 defines normal retention and intervention sensitivity gates
- M766 blocks training PPO and promotion

## Failure Criteria

- design uses contaminated assigned_split heldout as unbiased
- design admits training or PPO
- design lacks source freshness criteria
- design lacks normal retention metrics
- design treats holdout as promotion gate

## Evidence Gates

- M766 designs a fresh source-holdout replay plan
- M766 explicitly avoids using M755 assigned_split heldout as unbiased holdout
- M766 prioritizes alpha 0.2 and treats 0.5 1.0 as diagnostics
- M766 keeps no-PPO no-promotion scope
- M766 defines fallback to fresh v4 source mining if existing artifacts are insufficient

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not use M755 assigned_split heldout as unbiased holdout
- do not train residual or actor parameters
- do not run PPO
- do not promote a checkpoint
- do not tune alpha from holdout and call it unbiased
- do not claim true four-wheel or single-wheel physics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m766-v4-residual-source-holdout-replay-design
- type: infrastructure
- checkpoint: docs/m766-v4-residual-source-holdout-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_fresh_source_holdout_wave_design_admit_m767
- reason: M766 finds no clean extra M752/M755 positive holdout and designs disjoint-seed fresh source-holdout wave before residual replay

## Next Blocker

m767-v4-fresh-source-holdout-wave-implementation
