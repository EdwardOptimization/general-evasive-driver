# m781-v4-broader-normal-boundary-alpha-probe-audit Research Review

## Summary

- Generated at UTC: 20260525T022041Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_normal_margin_aware_residual_calibration_design
- Decision reason: M781 audits alpha 0.125 as a limited feasibility positive but not robust promotion evidence because active source margin is only about 9e-6; next is normal-margin-aware residual calibration design

## Hypothesis

M780 should be audited as a limited lower-alpha feasibility positive, but alpha 0.125's tiny boundary margin may require normal-margin-aware objective repair before any training or PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m780-v4-broader-normal-boundary-alpha-probe-implementation.md, runs/m780_v4_broader_normal_boundary_alpha_probe/summary.json, runs/m780_v4_broader_normal_boundary_alpha_probe/alpha_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv, docs/m779-v4-broader-normal-boundary-alpha-probe-design.md, docs/m778-v4-limited-broader-residual-replay-audit.md
- parent_config: experiments/manifests/m780-v4-broader-normal-boundary-alpha-probe-implementation.json, experiments/manifests/m779-v4-broader-normal-boundary-alpha-probe-design.json
- parent_objective: audit M780 lower-alpha feasibility and decide next blocker before repair PPO or promotion
- derived_from: m780-v4-broader-normal-boundary-alpha-probe-implementation
- blocked_by: m780-v4-broader-normal-boundary-alpha-probe-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M781 records alpha 0.125 strict normal retention and gap improvement
- M781 records alpha 0.15 and above normal collisions
- M781 records seed 77025/source_index 12 margin crossing
- M781 classifies remaining risk without promotion
- M781 admits only one next blocker

## Failure Criteria

- audit promotes a checkpoint
- audit admits PPO
- audit ignores normal-boundary margin
- audit treats alpha 0.125 as robust promotion evidence
- audit hides M773 hard-negative and current-model/proxy caveats

## Evidence Gates

- M781 audits M780 lower-alpha boundary probe
- M781 separates strict normal-retention feasibility from promotion readiness
- M781 classifies alpha 0.125 boundary margin risk
- M781 decides whether next step is alpha feasibility consolidation or normal-margin objective repair
- PPO training residual retraining and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not call alpha 0.125 robust without auditing its tiny boundary margin
- do not hide alpha 0.15 and above normal collisions
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m781-v4-broader-normal-boundary-alpha-probe-audit
- type: gate
- checkpoint: docs/m781-v4-broader-normal-boundary-alpha-probe-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_normal_margin_aware_residual_calibration_design
- reason: M781 audits alpha 0.125 as a limited feasibility positive but not robust promotion evidence because active source margin is only about 9e-6; next is normal-margin-aware residual calibration design

## Next Blocker

m782-v4-normal-margin-aware-residual-calibration-design
