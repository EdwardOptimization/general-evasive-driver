# m810-v4-low-margin-new-data-route-design Research Review

## Summary

- Generated at UTC: 20260525T065159Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: low_margin_new_data_route_design_admit_m811
- Decision reason: M810 designs active diagnostic warm-up plus joint obstacle fault timing data generation while preserving the primary margin and no-training gates

## Hypothesis

A new data route that combines active diagnostic history, joint obstacle/fault timing, and source-balanced near-boundary mining can target the missing low-margin source diversity better than more fixed-anchor retargeting.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m809-v4-low-margin-source-diverse-branch-synthesis.md, docs/m808-v4-low-margin-boundary-axis-expansion-audit.md, runs/m807_v4_low_margin_boundary_axis_expansion/summary.json, runs/m804_v4_low_margin_boundary_window_retarget/summary.json
- parent_config: experiments/manifests/m809-v4-low-margin-source-diverse-branch-synthesis.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design a new low-margin data route after closing the geometry-only retarget branch
- derived_from: m809-v4-low-margin-source-diverse-branch-synthesis
- blocked_by: m809-v4-low-margin-source-diverse-branch-synthesis
- supersedes: None
- invalidates: None

## Success Criteria

- M810 designs a concrete no-training data route
- M810 defines source fault and axis diversity gates before implementation
- M810 defines how active diagnostic history or warm-up evidence is collected without oracle actor inputs
- M810 records current-model proxy limits for future wheel-level faults
- M810 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- design admits calibration or PPO directly
- design reuses M804/M807 half-width rows as if they were source-diverse
- design weakens the primary low-margin threshold
- design adds deploy-time privileged inputs
- design overclaims current single-track proxy faults as true wheel-level physics

## Evidence Gates

- M810 designs only a new data route
- M810 does not weaken the primary low-margin threshold
- M810 preserves the P0 human-view no-wheel actor contract
- M810 keeps M804/M807 half-width rows as limited debug data only
- M810 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not weaken the primary 0.00005 margin threshold
- do not treat M804 or M807 half-width rows as a source-diverse pass
- do not claim true wheel-level faults from current single-track proxy data
- do not tune from private holdout failures

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m810-v4-low-margin-new-data-route-design
- type: infrastructure
- checkpoint: docs/m810-v4-low-margin-new-data-route-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_margin_new_data_route_design_admit_m811
- reason: M810 designs active diagnostic warm-up plus joint obstacle fault timing data generation while preserving the primary margin and no-training gates

## Next Blocker

m811-v4-low-margin-new-data-route-implementation
