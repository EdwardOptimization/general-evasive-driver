# m774-v4-broader-source-holdout-wave-audit Research Review

## Summary

- Generated at UTC: 20260525T013349Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_limited_broader_residual_replay_design
- Decision reason: M774 audits M773 as materially supporting the coverage-limited hypothesis while preserving strict broad-gate misses hard-negative sparsity and source concentration caveats before limited no-PPO residual replay design

## Hypothesis

M773's broader corpus should be audited before deciding whether to run limited residual replay or further improve source coverage.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m773-v4-broader-source-holdout-wave-implementation.md, runs/m773_v4_broader_source_holdout_extreme_faults/summary.json, runs/m773_v4_broader_source_holdout_sequence_intervention/summary.json, runs/m773_v4_broader_source_holdout_corpus_export/summary.json, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m773-v4-broader-source-holdout-wave-implementation.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: audit broader source-holdout corpus before residual replay or further source mining
- derived_from: m773-v4-broader-source-holdout-wave-implementation
- blocked_by: m773-v4-broader-source-holdout-wave-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M774 records which M772 broad gates passed and failed
- M774 records source and fault-family concentration
- M774 records hard-negative sparsity
- M774 records supported and falsified claims
- M774 admits only one next blocker without PPO or promotion

## Failure Criteria

- audit admits PPO or promotion
- audit hides source concentration or hard-negative sparsity
- audit overclaims broad generalization
- audit treats current-model proxies as true per-wheel physics

## Evidence Gates

- M774 audits M773 broader source wave against M772 broad gates
- M774 separates ordinary corpus validity from stricter broad-coverage adequacy
- M774 audits hard-negative sparsity and source dominance
- M774 decides between limited residual replay and more source-balancing work
- PPO training and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run residual replay in the audit
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not hide strict broad-gate misses
- do not claim true four-wheel or single-wheel physical fidelity

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m774-v4-broader-source-holdout-wave-audit
- type: gate
- checkpoint: docs/m774-v4-broader-source-holdout-wave-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_limited_broader_residual_replay_design
- reason: M774 audits M773 as materially supporting the coverage-limited hypothesis while preserving strict broad-gate misses hard-negative sparsity and source concentration caveats before limited no-PPO residual replay design

## Next Blocker

m775-v4-limited-broader-residual-replay-design
