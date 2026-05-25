# m778-v4-limited-broader-residual-replay-audit Research Review

## Summary

- Generated at UTC: 20260525T020615Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_broader_normal_boundary_alpha_probe_design
- Decision reason: M778 audits M777 as mechanism-positive but strict-normal-retention-failed: alpha 0.2 improves intervention action gap and margin gap but creates one unique near-boundary normal collision source; next is a pre-registered lower-alpha normal-boundary probe with PPO and promotion blocked

## Hypothesis

M777's alpha 0.2 broader replay result should be audited as mechanism-positive but strict-normal-retention-failed due to a concentrated near-boundary source.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m777-v4-limited-broader-residual-replay-implementation.md, runs/m777_v4_limited_broader_residual_replay/summary.json, runs/m777_v4_limited_broader_residual_replay/alpha_metrics.csv, runs/m777_v4_limited_broader_residual_replay/replay_rows.csv, runs/m773_v4_broader_source_holdout_corpus_export/summary.json
- parent_config: experiments/manifests/m777-v4-limited-broader-residual-replay-implementation.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: audit broader residual replay normal-retention regression before repair or retuning
- derived_from: m777-v4-limited-broader-residual-replay-implementation
- blocked_by: m777-v4-limited-broader-residual-replay-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M778 records alpha 0.2 action-gap and margin-gap improvements
- M778 records strict normal-retention failure
- M778 identifies collision concentration
- M778 classifies failure taxonomy
- M778 admits only one next blocker without PPO promotion or alpha retuning

## Failure Criteria

- audit treats script candidate pass as strict pass
- audit hides normal collisions
- audit tunes alpha retroactively
- audit admits PPO or promotion

## Evidence Gates

- M778 audits M777 broader residual replay
- M778 separates script candidate status from stricter M775 normal-retention gate
- M778 classifies the normal-branch collision source
- M778 decides whether to repair near-boundary normal retention or re-mine sources
- PPO training alpha retuning and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not tune alpha in the audit
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not hide alpha 0.2 normal collisions
- do not claim broad generalization

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m778-v4-limited-broader-residual-replay-audit
- type: gate
- checkpoint: docs/m778-v4-limited-broader-residual-replay-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_broader_normal_boundary_alpha_probe_design
- reason: M778 audits M777 as mechanism-positive but strict-normal-retention-failed: alpha 0.2 improves intervention action gap and margin gap but creates one unique near-boundary normal collision source; next is a pre-registered lower-alpha normal-boundary probe with PPO and promotion blocked

## Next Blocker

m779-v4-broader-normal-boundary-alpha-probe-design
