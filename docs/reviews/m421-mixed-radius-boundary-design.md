# m421-mixed-radius-boundary-design Research Review

## Summary

- Generated at UTC: 20260523T171524Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m422_mixed_radius_anchor_export_implementation
- Decision reason: M421 designs mixed_a mixed_b and mixed_c radius profiles after M420: tighten old-key 10023 first then loosen 10004 and M267 rows only if proof remains safe

## Hypothesis

A mixed per-case radius profile can preserve the M420 conservative proof pass while recovering more of the M420 medium utility movement by tightening only the active old-key 10023 boundary and loosening non-boundary rows.

## Lineage

- parent_checkpoint: runs/m420_medium_radius_projection_ltraj1e13_s40_seed10150/candidate_checkpoint.pt, runs/m420_conservative_radius_projection_ltraj1e13_s40_seed10151/candidate_checkpoint.pt
- parent_dataset: runs/m420_medium_old_key_targeted_replay/guard_results.csv, runs/m420_conservative_old_key_replay_gate/summary.json, runs/m420_conservative_m267_m264_first_replay/summary.json, runs/m420_conservative_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m420-active-set-radius-projection-probe.json
- parent_objective: design mixed per-case radius profile after medium old-key boundary and conservative utility shortfall
- derived_from: m420-active-set-radius-projection-probe
- blocked_by: m420-active-set-radius-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- identify the exact M420 medium proof-failing row and branch
- define a mixed radius profile with 10023 tightened and non-boundary rows allowed more slack
- pre-register the next export/probe sequence without PPO
- keep primary M420 proof and utility thresholds unchanged

## Failure Criteria

- design lowers proof thresholds
- design ignores the M420 medium old-key failure
- design lacks utility-retention criterion
- design requires PPO or actor input changes

## Evidence Gates

- design only
- no PPO run
- no projection run
- no checkpoint promotion
- no actor input/output change

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

- milestone: m421-mixed-radius-boundary-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m422_mixed_radius_anchor_export_implementation
- reason: M421 designs mixed_a mixed_b and mixed_c radius profiles after M420: tighten old-key 10023 first then loosen 10004 and M267 rows only if proof remains safe

## Next Blocker

m422-mixed-radius-anchor-export-implementation
