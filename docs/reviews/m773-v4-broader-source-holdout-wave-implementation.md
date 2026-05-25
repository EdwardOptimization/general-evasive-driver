# m773-v4-broader-source-holdout-wave-implementation Research Review

## Summary

- Generated at UTC: 20260525T012955Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: v4_sequence_outcome_corpus_hard_negative_sparse
- Decision reason: M773 exports 2652 clean positives with 49 seeds 17 fault-family pairs max seed dominance 0.171569 max pair dominance 0.208145 and no sentinel or metadata artifacts while residual replay PPO and promotion remain blocked

## Hypothesis

A larger fresh v4 source-holdout wave can produce a less concentrated corpus and test whether sparse coverage was limiting the residual self-ID evidence.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m772-v4-broader-source-holdout-wave-design.md, runs/m770_v4_limited_residual_holdout_replay/summary.json, runs/m767_v4_source_holdout_corpus_export/summary.json
- parent_config: experiments/manifests/m772-v4-broader-source-holdout-wave-design.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: run broader no-training source-holdout wave before any residual replay or PPO
- derived_from: m772-v4-broader-source-holdout-wave-design
- blocked_by: m772-v4-broader-source-holdout-wave-design
- supersedes: None
- invalidates: None

## Success Criteria

- M773 runs the broader v4 extreme-fault source wave
- M773 runs broader v4 reset-source sequence interventions
- M773 exports a broader v4 sequence-outcome corpus
- M773 reports broad gates: positive_rows unique_positive_seeds unique_positive_fault_family_pairs seed dominance and fault-pair dominance
- M773 does not run residual replay PPO training or promotion

## Failure Criteria

- fresh seed range overlaps previous v4 source waves
- residual replay is run before corpus audit
- training or PPO starts
- fresh corpus metadata is missing
- positive rows remain too sparse or source-concentrated for broad holdout claims

## Evidence Gates

- M773 uses seed range 77024..78047 disjoint from M749/M752/M767
- M773 uses configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- M773 increases max_pairs to 24576 and max_source_rows to 1024
- M773 exports a broader fresh v4 sequence-outcome corpus
- M773 reports broader gates: positives seeds fault-family pairs and dominance
- residual replay PPO training and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not reuse M755 M767 or M770 rows as fresh broad holdout rows
- do not train actor or residual parameters
- do not run residual closed-loop replay in M773
- do not run PPO
- do not promote a checkpoint
- do not tune thresholds after seeing the output
- do not claim true four-wheel or single-wheel physical fidelity

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m773-v4-broader-source-holdout-wave-implementation
- type: generalization
- checkpoint: runs/m773_v4_broader_source_holdout_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_outcome_corpus_hard_negative_sparse
- reason: M773 exports 2652 clean positives with 49 seeds 17 fault-family pairs max seed dominance 0.171569 max pair dominance 0.208145 and no sentinel or metadata artifacts while residual replay PPO and promotion remain blocked

## Next Blocker

m774-v4-broader-source-holdout-wave-audit
