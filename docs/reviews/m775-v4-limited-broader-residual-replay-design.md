# m775-v4-limited-broader-residual-replay-design Research Review

## Summary

- Generated at UTC: 20260525T013925Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: limited_broader_residual_replay_design_admit_synthesis
- Decision reason: M775 designs no-PPO residual replay on the M773 broader corpus while routing the branch to required workflow synthesis before implementation

## Hypothesis

A limited no-PPO residual replay on the broader M773 corpus can test whether the M761 residual mechanism transfers beyond the sparse M767 holdout.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m774-v4-broader-source-holdout-wave-audit.md, runs/m773_v4_broader_source_holdout_corpus_export/summary.json, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m774-v4-broader-source-holdout-wave-audit.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: design limited no-PPO residual replay on broader M773 corpus
- derived_from: m774-v4-broader-source-holdout-wave-audit
- blocked_by: m774-v4-broader-source-holdout-wave-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M775 fixes replay inputs to M761 residual head and M773 positive/contrast rows
- M775 sets alpha 0.2 as the primary conservative candidate
- M775 keeps 0.5 and 1.0 diagnostic
- M775 requires seed fault-family variant and horizon stratification
- M775 blocks PPO training and promotion
- M775 admits workflow synthesis before implementation

## Failure Criteria

- design admits PPO or promotion
- design changes actor or residual weights
- design tunes alpha from M773 outcomes
- design hides M773 source concentration or hard-negative sparsity

## Evidence Gates

- M775 designs limited no-PPO residual replay on M773 broader corpus
- M775 uses alpha 0.2 as primary and 0.5 1.0 as diagnostic
- M775 preserves M773 concentration and hard-negative caveats
- M775 requires normal branch retention and intervention sensitivity metrics
- training PPO and checkpoint promotion remain blocked
- M775 sends the branch to workflow synthesis before replay implementation

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not tune alpha from M773 results before replay
- do not hide broad-gate misses or hard-negative sparsity
- do not claim true four-wheel or single-wheel physical fidelity

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m775-v4-limited-broader-residual-replay-design
- type: infrastructure
- checkpoint: docs/m775-v4-limited-broader-residual-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: limited_broader_residual_replay_design_admit_synthesis
- reason: M775 designs no-PPO residual replay on the M773 broader corpus while routing the branch to required workflow synthesis before implementation

## Next Blocker

m776-v4-residual-source-holdout-replay-synthesis
