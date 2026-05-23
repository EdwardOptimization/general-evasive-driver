# m419-active-set-radius-anchor-export-implementation Research Review

## Summary

- Generated at UTC: 20260523T170617Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m420_active_set_radius_projection_probe
- Decision reason: M419 exports conservative medium and loose 274-row radius anchors with 82 old-key spillover rows; all no-update exact repair smokes pass with zero exact deltas

## Hypothesis

The M418 radius profiles can be exported as explicit trajectory-anchor radii, including M417 old-key spillover guard rows, without changing actor inputs or exact-repair feasibility.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m416_active_set_hinge_anchor/active_set_hinge_trajectory_anchor.npz, runs/m417_hinge_old_key_targeted_replay/guard_results.csv, docs/m418-active-set-radius-calibration-design.md
- parent_config: experiments/manifests/m418-active-set-radius-calibration-design.json
- parent_objective: export active-set v2 anchors with explicit per-row radius profiles
- derived_from: m418-active-set-radius-calibration-design
- blocked_by: m417-active-set-hinge-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- export conservative, medium, and loose radius anchor NPZs
- each anchor contains M416 active rows plus M417 old-key spillover guards
- each exported row has an explicit finite nonnegative radius
- no-update exact repair smoke passes exact M297/M270/old-key no-regression for each profile
- focused tests or validation cover the radius export path

## Failure Criteria

- radius anchor export omits active or spillover rows
- radius values are missing, nonfinite, or negative
- no-update exact repair smoke regresses exact objectives
- implementation changes actor inputs or outputs
- milestone runs projection or PPO instead of export-only validation

## Evidence Gates

- no-update exact repair smoke for conservative radius anchor
- no-update exact repair smoke for medium radius anchor
- no-update exact repair smoke for loose radius anchor
- no PPO run
- no checkpoint promotion
- no actor input/output change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run projection proof probe
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m419-active-set-radius-anchor-export-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m420_active_set_radius_projection_probe
- reason: M419 exports conservative medium and loose 274-row radius anchors with 82 old-key spillover rows; all no-update exact repair smokes pass with zero exact deltas

## Next Blocker

m420-active-set-radius-projection-probe
