# m422-mixed-radius-anchor-export-implementation Research Review

## Summary

- Generated at UTC: 20260523T171946Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m423_mixed_radius_projection_probe
- Decision reason: M422 extends the radius exporter to mixed profiles and exports mixed_a mixed_b mixed_c 274-row anchors; all no-update exact repair smokes pass

## Hypothesis

Mixed-radius anchors can be exported by tightening old-key 10023 while keeping or loosening non-boundary rows, without changing actor inputs or exact-repair feasibility.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m419_active_set_radius_anchor/radius_anchor_sources.csv, runs/m419_active_set_radius_anchor/medium_radius_anchor.npz, runs/m419_active_set_radius_anchor/conservative_radius_anchor.npz, runs/m419_active_set_radius_anchor/loose_radius_anchor.npz, docs/m421-mixed-radius-boundary-design.md
- parent_config: experiments/manifests/m421-mixed-radius-boundary-design.json
- parent_objective: export mixed per-case radius anchors after M420 old-key 10023 boundary
- derived_from: m421-mixed-radius-boundary-design
- blocked_by: m420-active-set-radius-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- export mixed_a, mixed_b, and mixed_c radius anchor NPZs
- mixed_a uses medium radii except conservative radius for 10023
- mixed_b additionally uses loose radius for 10004
- mixed_c additionally uses loose radius for M267 rows 6 and 15
- no-update exact repair smoke passes exact M297/M270/old-key no-regression for each profile

## Failure Criteria

- mixed radius export omits active-set v2 rows
- radius values are missing, nonfinite, or negative
- no-update exact repair smoke regresses exact objectives
- implementation changes actor inputs or outputs
- milestone runs projection or PPO instead of export-only validation

## Evidence Gates

- no-update exact repair smoke for mixed_a anchor
- no-update exact repair smoke for mixed_b anchor
- no-update exact repair smoke for mixed_c anchor
- no PPO run
- no projection run
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

- milestone: m422-mixed-radius-anchor-export-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m423_mixed_radius_projection_probe
- reason: M422 extends the radius exporter to mixed profiles and exports mixed_a mixed_b mixed_c 274-row anchors; all no-update exact repair smokes pass

## Next Blocker

m423-mixed-radius-projection-probe
