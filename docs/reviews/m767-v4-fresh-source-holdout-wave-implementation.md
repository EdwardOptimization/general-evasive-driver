# m767-v4-fresh-source-holdout-wave-implementation Research Review

## Summary

- Generated at UTC: 20260525T004708Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: v4_sequence_outcome_corpus_sparse
- Decision reason: M767 fresh disjoint-seed wave exports 995 clean positives with no sentinel positives but fails fresh corpus gate due positive count 995 fault-pair diversity 13 and seed dominance 0.247236

## Hypothesis

A disjoint-seed v4 source-holdout wave can produce a fresh sequence-outcome corpus suitable for later M761 residual replay.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m766-v4-residual-source-holdout-replay-design.md, runs/m764_v4_residual_closed_loop_replay/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv, runs/m749_extreme_fault_distribution_v4/summary.json
- parent_config: experiments/manifests/m766-v4-residual-source-holdout-replay-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: run fresh no-training source-holdout wave before residual replay
- derived_from: m766-v4-residual-source-holdout-replay-design
- blocked_by: m766-v4-residual-source-holdout-replay-design
- supersedes: None
- invalidates: None

## Success Criteria

- M767 runs the fresh v4 extreme-fault source wave
- M767 runs fresh v4 reset-source sequence interventions
- M767 exports a fresh v4 sequence-outcome corpus
- M767 reports whether minimum fresh corpus gates pass
- M767 does not run residual replay PPO or promotion

## Failure Criteria

- fresh seed range overlaps M749/M752
- residual replay is run before fresh corpus audit
- training or PPO starts
- fresh corpus metadata is missing
- positive rows are too sparse to support holdout replay

## Evidence Gates

- M767 uses seed range 76512..77023 disjoint from M749/M752
- M767 runs no-training v4 source wave and sequence intervention
- M767 exports a fresh v4 sequence-outcome corpus
- M767 reports source diversity and hard-negative sparsity
- residual replay PPO and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not reuse M755 assigned_split heldout as unbiased holdout
- do not train actor or residual parameters
- do not run residual closed-loop replay in M767
- do not run PPO
- do not promote a checkpoint
- do not lower fresh corpus gates after seeing output

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m767-v4-fresh-source-holdout-wave-implementation
- type: generalization
- checkpoint: runs/m767_v4_source_holdout_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_outcome_corpus_sparse
- reason: M767 fresh disjoint-seed wave exports 995 clean positives with no sentinel positives but fails fresh corpus gate due positive count 995 fault-pair diversity 13 and seed dominance 0.247236

## Next Blocker

m768-v4-fresh-source-holdout-wave-audit
