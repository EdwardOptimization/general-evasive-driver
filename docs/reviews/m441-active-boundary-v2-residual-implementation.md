# m441-active-boundary-v2-residual-implementation Research Review

## Summary

- Generated at UTC: 20260523T190609Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m442_active_boundary_v2_projection_probe
- Decision reason: M441 exports a 36-row v2 active-boundary window corpus wires v2 exact repair terms and passes no-update smoke with exact no-regression

## Hypothesis

The active-boundary v2 trajectory-window corpus and row-specific exact terms can be implemented as training-only repair machinery without changing the deployable actor contract.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt
- parent_dataset: runs/m439_active_boundary_residual_utility_audit/policy_utility_summary.csv, runs/m439_active_boundary_residual_utility_audit/active_case_rows.csv, runs/m437_active_boundary_residual/active_boundary_corpus.npz
- parent_config: experiments/manifests/m440-active-boundary-v2-residual-design.json
- parent_objective: active-boundary v2 residual implementation
- derived_from: m440-active-boundary-v2-residual-design
- blocked_by: m440-active-boundary-v2-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- export v2 rows for 10004 10023 and 9998 active cases when snapshots are present
- loader validates trajectory-window shapes weights and finite fields
- exact terms cover wrong-history safety gap erosion and normal safety families
- no-update exact repair smoke loads v2 corpus and passes exact no-regression

## Failure Criteria

- v2 corpus degenerates into broad full-trajectory imitation
- implementation changes actor inputs or outputs
- no-update smoke fails
- implementation requires PPO or projection to validate

## Evidence Gates

- export active-boundary v2 trajectory-window corpus
- loader and exact loss tests
- no-update exact repair smoke
- no actor input or output contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run projection
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m441-active-boundary-v2-residual-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m442_active_boundary_v2_projection_probe
- reason: M441 exports a 36-row v2 active-boundary window corpus wires v2 exact repair terms and passes no-update smoke with exact no-regression

## Next Blocker

m442-active-boundary-v2-projection-probe
