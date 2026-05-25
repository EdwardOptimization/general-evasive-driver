# m819-v4-adaptive-primary-calibration-followup-design Research Review

## Summary

- Generated at UTC: 20260525T091113Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: adaptive_primary_calibration_followup_design_admit_branch_synthesis
- Decision reason: M819 designs non-PPO source-heldout calibration follow-up with fixed scalar vector and adaptive gate comparisons then routes to branch synthesis before implementation

## Hypothesis

A stronger follow-up must first design an exact, source-heldout non-PPO comparison that separates identity retention from genuine adaptive residual calibration.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m818-v4-adaptive-primary-residual-calibration-audit.md, runs/m817_v4_adaptive_primary_residual_calibration/summary.json, runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv, runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv
- parent_config: experiments/manifests/m818-v4-adaptive-primary-residual-calibration-audit.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design informative non-PPO adaptive primary calibration follow-up
- derived_from: m818-v4-adaptive-primary-residual-calibration-audit
- blocked_by: m817 near-identity calibrator validates retention harness but does not prove useful adaptation
- supersedes: None
- invalidates: None

## Success Criteria

- M819 writes a design document for the next calibration probe
- M819 defines fixed-gate, vector-gate, and adaptive-gate comparisons without PPO
- M819 defines train-only objective selection and holdout exact acceptance gates
- M819 defines normal-margin lift and intervention-sensitivity retention criteria
- M819 routes to branch synthesis before implementation

## Failure Criteria

- M819 starts implementation or training
- M819 allows actor or residual-head updates
- M819 allows PPO
- M819 treats M817 near-identity gates as performance improvement
- M819 skips source-heldout exact gates
- M819 continues the branch without synthesis

## Evidence Gates

- M819 must remain design-only
- M819 must keep actor and M761 residual-head training blocked
- M819 must keep PPO and promotion blocked
- M819 must distinguish identity-retention from performance improvement
- M819 must require source-heldout exact gates for any follow-up implementation
- M819 must route to branch synthesis before a new implementation milestone

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not widen the primary 0.00005 margin threshold
- do not use holdout rows for training objective selection
- do not claim a useful adaptive calibrator from near-identity gates
- do not add oracle deploy-time inputs
- do not continue the branch past synthesis cadence without a synthesis milestone

## Failure Taxonomy

- metric_artifact
- objective_overfit
- behavior_regression

## Scoreboard

- milestone: m819-v4-adaptive-primary-calibration-followup-design
- type: infrastructure
- checkpoint: docs/m819-v4-adaptive-primary-calibration-followup-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: adaptive_primary_calibration_followup_design_admit_branch_synthesis
- reason: M819 designs non-PPO source-heldout calibration follow-up with fixed scalar vector and adaptive gate comparisons then routes to branch synthesis before implementation

## Next Blocker

m820-v4-low-margin-new-data-route-branch-synthesis
