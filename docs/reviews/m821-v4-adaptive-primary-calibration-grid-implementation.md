# m821-v4-adaptive-primary-calibration-grid-implementation Research Review

## Summary

- Generated at UTC: 20260525T095202Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_adaptive_primary_calibration_identity_only
- Decision reason: M821 evaluates 53 fixed scalar/vector residual gate candidates under source-heldout exact replay and selects identity; no nonidentity gate gives positive margin lift while preserving gates

## Hypothesis

A fixed scalar or vector residual gate may produce nontrivial normal-margin lift over identity while preserving source-heldout intervention sensitivity and old behavior.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m820-v4-low-margin-new-data-route-branch-synthesis.md, docs/m819-v4-adaptive-primary-calibration-followup-design.md, runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv, runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv, runs/m817_v4_adaptive_primary_residual_calibration/split_rows.csv
- parent_config: experiments/manifests/m820-v4-low-margin-new-data-route-branch-synthesis.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement exact non-PPO calibration grid over source-heldout M814 rows
- derived_from: m820-v4-low-margin-new-data-route-branch-synthesis
- blocked_by: need exact fixed scalar/vector residual gate grid to test M819 design
- supersedes: None
- invalidates: None

## Success Criteria

- M821 implements source-heldout exact calibration grid evaluation
- M821 writes summary grid train holdout intervention and gate artifacts
- M821 compares identity fixed scalar and fixed vector gates
- M821 selects candidates on train rows only
- M821 evaluates holdout rows exactly
- M821 verifies actor and residual-head checksums unchanged
- M821 keeps PPO and promotion blocked

## Failure Criteria

- M821 trains actor or M761 residual-head parameters
- M821 trains an adaptive calibrator
- M821 runs PPO
- M821 promotes a checkpoint
- M821 selects candidates from holdout rows
- M821 weakens primary threshold
- M821 ignores intervention sensitivity or old behavior drift

## Evidence Gates

- M821 must implement exact non-PPO grid evaluation only
- M821 must not train actor parameters
- M821 must not train M761 residual-head parameters
- M821 must not run PPO
- M821 must not promote a checkpoint
- M821 must select candidate gates on train rows only
- M821 must evaluate holdout rows exactly after train selection
- M821 must classify identity-only train-overfit intervention-washout old-behavior-regression or candidate result

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not train an adaptive calibrator in M821
- do not run PPO
- do not promote a checkpoint
- do not widen the primary 0.00005 margin threshold
- do not use holdout rows for candidate selection
- do not claim driver improvement from train-only lift
- do not add oracle deploy-time inputs
- do not claim true wheel-level mechanical faults from current proxy data

## Failure Taxonomy

- metric_artifact
- objective_overfit
- behavior_regression
- contract_violation

## Scoreboard

- milestone: m821-v4-adaptive-primary-calibration-grid-implementation
- type: infrastructure
- checkpoint: runs/m821_v4_adaptive_primary_calibration_grid/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_adaptive_primary_calibration_identity_only
- reason: M821 evaluates 53 fixed scalar/vector residual gate candidates under source-heldout exact replay and selects identity; no nonidentity gate gives positive margin lift while preserving gates

## Next Blocker

m822-v4-adaptive-primary-calibration-grid-audit
