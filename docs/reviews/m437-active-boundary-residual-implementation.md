# m437-active-boundary-residual-implementation Research Review

## Summary

- Generated at UTC: 20260523T184132Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m438_active_boundary_projection_probe
- Decision reason: M437 exports a 6-row active-boundary corpus covering 10004 10023 and 9998 wires exact repair terms and passes no-update smoke with exact no-regression

## Hypothesis

A compact active-boundary preference residual can be implemented as training-only exact repair machinery without changing the deployable actor contract.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt, runs/m434_selective_10004_projection_r0015/candidate_checkpoint.pt
- parent_dataset: runs/m434_r0015_old_key_targeted_replay/guard_results.csv, runs/m434_r0020_old_key_targeted_replay/guard_results.csv, runs/m434_tail_r0010_old_key_targeted_replay/guard_results.csv
- parent_config: experiments/manifests/m436-old-key-active-boundary-residual-design.json
- parent_objective: active-boundary old-key residual implementation
- derived_from: m436-old-key-active-boundary-residual-design
- blocked_by: m436-old-key-active-boundary-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- corpus exporter writes finite active-boundary rows for 10004 10023 and 9998 when present
- loader validates shapes and finite fields
- exact loss terms are covered by focused tests
- no-update exact repair smoke passes

## Failure Criteria

- corpus cannot represent gap erosion and wrong-history safety separately
- implementation changes actor inputs or outputs
- no-update exact repair smoke fails
- implementation requires PPO to validate

## Evidence Gates

- export active-boundary corpus
- loader and exact loss tests
- no-update exact repair smoke
- no actor input or output contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m437-active-boundary-residual-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m438_active_boundary_projection_probe
- reason: M437 exports a 6-row active-boundary corpus covering 10004 10023 and 9998 wires exact repair terms and passes no-update smoke with exact no-regression

## Next Blocker

m438-active-boundary-projection-probe
