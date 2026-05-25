# m771-v4-limited-residual-holdout-replay-audit Research Review

## Summary

- Generated at UTC: 20260525T005749Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_broader_source_holdout_wave_design
- Decision reason: M771 audits M770 as limited holdout mechanism positive and selects broader source-holdout coverage before stronger generalization PPO or promotion claims

## Hypothesis

M770 is a limited source-holdout mechanism positive that should be audited before broader source coverage or PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m770-v4-limited-residual-holdout-replay-implementation.md, runs/m770_v4_limited_residual_holdout_replay/summary.json, runs/m770_v4_limited_residual_holdout_replay/alpha_metrics.csv, runs/m770_v4_limited_residual_holdout_replay/objective_rows.csv, runs/m767_v4_source_holdout_corpus_export/summary.json
- parent_config: experiments/manifests/m770-v4-limited-residual-holdout-replay-implementation.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: audit limited residual holdout replay before broader source wave or PPO
- derived_from: m770-v4-limited-residual-holdout-replay-implementation
- blocked_by: m770-v4-limited-residual-holdout-replay-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M771 reviews alpha metrics and collision concentration
- M771 records supported and falsified claims
- M771 classifies source sparsity risks
- M771 chooses the next branch without PPO or promotion

## Failure Criteria

- audit overclaims broad generalization
- audit ignores collision concentration
- audit admits PPO or promotion
- audit ignores claim-boundary limits

## Evidence Gates

- M771 reviews M770 limited holdout replay
- M771 separates normal retention from intervention collision sensitivity
- M771 audits sparse-source and collision concentration risks
- M771 decides between broader source wave and residual replay continuation
- PPO and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not treat M770 as broad generalization
- do not run PPO
- do not promote a checkpoint
- do not ignore source sparsity
- do not ignore intervention collision concentration
- do not claim true four-wheel or single-wheel physics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m771-v4-limited-residual-holdout-replay-audit
- type: gate
- checkpoint: docs/m771-v4-limited-residual-holdout-replay-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_broader_source_holdout_wave_design
- reason: M771 audits M770 as limited holdout mechanism positive and selects broader source-holdout coverage before stronger generalization PPO or promotion claims

## Next Blocker

m772-v4-broader-source-holdout-wave-design
