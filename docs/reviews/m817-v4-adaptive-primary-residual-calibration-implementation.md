# m817-v4-adaptive-primary-residual-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260525T083511Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_adaptive_primary_residual_calibration_candidate
- Decision reason: M817 trains only a near-identity scalar residual calibrator with source-heldout split; train and holdout normal rows stay collision-free intervention collision rates are retained and action drift is near zero with no actor residual-head PPO or promotion

## Hypothesis

A small separate residual calibrator can preserve M814 primary normal rows and intervention sensitivity on a source-heldout split without changing actor or residual-head weights.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m816-v4-adaptive-primary-residual-calibration-design.md, runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv, runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv
- parent_config: experiments/manifests/m816-v4-adaptive-primary-residual-calibration-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement source-heldout residual calibration probe
- derived_from: m816-v4-adaptive-primary-residual-calibration-design
- blocked_by: need source-heldout calibration implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M817 writes split training evaluation calibrator summary and documentation artifacts
- M817 confirms actor and M761 residual-head checksums unchanged
- M817 reports train and holdout normal/intervention exact metrics
- M817 reports old replay or behavior retention metrics
- M817 classifies the result without promoting a checkpoint

## Failure Criteria

- implementation updates actor weights
- implementation updates M761 residual-head weights
- implementation trains on holdout rows
- implementation runs PPO
- implementation promotes a checkpoint
- implementation weakens the primary margin threshold

## Evidence Gates

- M817 may train only a separate residual calibrator
- M817 must not update actor or M761 residual-head parameters
- M817 must create and respect source-heldout split before optimization
- M817 must run train and holdout exact gates
- M817 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not widen the primary 0.00005 margin threshold
- do not train on holdout rows
- do not tune from private holdout failures
- do not claim true wheel-level faults from current proxy data

## Failure Taxonomy

- objective_overfit
- metric_artifact
- contract_violation
- behavior_regression

## Scoreboard

- milestone: m817-v4-adaptive-primary-residual-calibration-implementation
- type: infrastructure
- checkpoint: runs/m817_v4_adaptive_primary_residual_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_adaptive_primary_residual_calibration_candidate
- reason: M817 trains only a near-identity scalar residual calibrator with source-heldout split; train and holdout normal rows stay collision-free intervention collision rates are retained and action drift is near zero with no actor residual-head PPO or promotion

## Next Blocker

m818-v4-adaptive-primary-residual-calibration-audit
