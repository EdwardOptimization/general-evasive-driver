# m816-v4-adaptive-primary-residual-calibration-design Research Review

## Summary

- Generated at UTC: 20260525T074424Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: adaptive_primary_residual_calibration_design_admit_m817
- Decision reason: M816 designs a source-heldout residual calibration probe with separate identity-regularized scalar/vector gate normal primary retention intervention sensitivity retention old-gate checks and no actor residual-head PPO or promotion

## Hypothesis

A residual calibration design can use the M814 adaptive primary corpus safely if it includes source-heldout split, normal-margin retention, intervention sensitivity retention, and old-gate replay checks.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m815-v4-adaptive-boundary-bracketing-audit.md, runs/m814_v4_adaptive_boundary_bracketing/summary.json, runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv, runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv
- parent_config: experiments/manifests/m815-v4-adaptive-boundary-bracketing-audit.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design source-heldout residual calibration using M814 adaptive primary corpus
- derived_from: m815-v4-adaptive-boundary-bracketing-audit
- blocked_by: need calibration design with source-heldout and retention gates
- supersedes: None
- invalidates: None

## Success Criteria

- M816 specifies train and holdout split rules
- M816 specifies calibration objective and exact gates
- M816 specifies old-gate and behavior retention checks
- M816 preserves no-PPO and no-promotion invariants
- M816 names the implementation blocker explicitly

## Failure Criteria

- M816 admits training without holdout
- M816 updates actor weights
- M816 starts PPO or promotes a checkpoint
- M816 weakens the primary margin threshold
- M816 ignores current-model proxy-fault limitations

## Evidence Gates

- M816 is design-only
- M816 must preserve the P0 human-view actor contract
- M816 must keep actor and residual-head base weights frozen in the design unless a separate calibrator is explicitly proposed
- M816 must define source-heldout split and old-gate retention before implementation
- M816 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not widen the primary 0.00005 margin threshold
- do not ignore source-heldout split
- do not tune from private holdout failures
- do not claim true wheel-level faults from current proxy data

## Failure Taxonomy

- objective_overfit
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m816-v4-adaptive-primary-residual-calibration-design
- type: infrastructure
- checkpoint: docs/m816-v4-adaptive-primary-residual-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: adaptive_primary_residual_calibration_design_admit_m817
- reason: M816 designs a source-heldout residual calibration probe with separate identity-regularized scalar/vector gate normal primary retention intervention sensitivity retention old-gate checks and no actor residual-head PPO or promotion

## Next Blocker

m817-v4-adaptive-primary-residual-calibration-implementation
