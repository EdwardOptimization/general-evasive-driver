# m772-v4-broader-source-holdout-wave-design Research Review

## Summary

- Generated at UTC: 20260525T010734Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: broader_source_holdout_wave_design_admit_m773
- Decision reason: M772 designs broader source-holdout coverage with seed range 77024..78047 max_pairs 24576 max_source_rows 1024 stricter diversity targets and explicit current-model proxy versus future high-fidelity fault boundaries

## Hypothesis

A broader fresh source-holdout wave can reduce source concentration and support stronger residual generalization evidence after M770's limited holdout positive.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m771-v4-limited-residual-holdout-replay-audit.md, runs/m770_v4_limited_residual_holdout_replay/summary.json, runs/m770_v4_limited_residual_holdout_replay/alpha_metrics.csv, runs/m767_v4_source_holdout_corpus_export/summary.json
- parent_config: experiments/manifests/m771-v4-limited-residual-holdout-replay-audit.json, configs/extreme_fault_distribution_v4_scenarios.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: design broader fresh source-holdout wave after limited holdout positive
- derived_from: m771-v4-limited-residual-holdout-replay-audit
- blocked_by: m771-v4-limited-residual-holdout-replay-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M772 defines fresh seed/source plan
- M772 defines diversity and dominance targets
- M772 defines no-training/no-PPO constraints
- M772 blocks residual replay until fresh corpus audit
- M772 admits only implementation as next step

## Failure Criteria

- design admits PPO or promotion
- design reuses contaminated holdout rows
- design lacks diversity gates
- design treats M770 as broad generalization evidence

## Evidence Gates

- M772 designs broader fresh source-holdout coverage
- M772 targets lower source dominance and higher fault-pair diversity
- M772 keeps no-training no-PPO no-promotion scope
- M772 preserves alpha 0.2 as primary for later replay
- M772 records current-model proxy versus future high-fidelity fault boundaries
- M772 does not treat M770 as promotion evidence

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not train actor or residual parameters
- do not reuse M755 or M767 as fresh broad holdout
- do not hide source concentration
- do not claim true four-wheel or single-wheel physics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m772-v4-broader-source-holdout-wave-design
- type: infrastructure
- checkpoint: docs/m772-v4-broader-source-holdout-wave-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: broader_source_holdout_wave_design_admit_m773
- reason: M772 designs broader source-holdout coverage with seed range 77024..78047 max_pairs 24576 max_source_rows 1024 stricter diversity targets and explicit current-model proxy versus future high-fidelity fault boundaries

## Next Blocker

m773-v4-broader-source-holdout-wave-implementation
