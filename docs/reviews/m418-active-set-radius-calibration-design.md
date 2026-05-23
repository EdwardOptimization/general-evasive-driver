# m418-active-set-radius-calibration-design Research Review

## Summary

- Generated at UTC: 20260523T165926Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m419_active_set_radius_anchor_export_implementation
- Decision reason: M418 designs active-set v2 radius profiles from M417 action-distance brackets and adds old-key spillover guards 9951 and 9939 before a no-PPO radius probe

## Hypothesis

Nonzero per-row hinge radii can avoid the M417 zero-radius proof/utility hard switch.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m417_active_set_hinge_projection_ltraj1e12_s40_seed10147/candidate_checkpoint.pt, runs/m417_active_set_hinge_projection_ltraj1e13_s40_seed10148/candidate_checkpoint.pt
- parent_dataset: runs/m417_active_set_hinge_utility_audit/summary.json, runs/m417_hinge_m267_m264_first_replay/summary.json, runs/m417_hinge1e13_m267_m264_first_replay/summary.json, runs/m417_hinge_old_key_replay_gate/summary.json, runs/m417_hinge1e13_old_key_replay_gate/summary.json
- parent_config: experiments/manifests/m417-active-set-hinge-projection-probe.json
- parent_objective: design nonzero radius calibration after zero-radius active-set proof/utility split
- derived_from: m417-active-set-hinge-projection-probe
- blocked_by: m417-active-set-hinge-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- define how to set per-row radii from M417 1e12 and 1e13 action distances
- define a no-PPO radius-sweep probe with exact gates, proof gates, and recovery-retention utility
- pre-register acceptance thresholds before running the probe

## Failure Criteria

- design falls back to another scalar-only weight sweep
- design weakens proof gates
- design lacks recovery utility criterion
- design requires PPO

## Evidence Gates

- design only
- no PPO run
- no checkpoint promotion
- no actor input/output change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not tune against private holdout

## Failure Taxonomy

- none

## Scoreboard

- milestone: m418-active-set-radius-calibration-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m419_active_set_radius_anchor_export_implementation
- reason: M418 designs active-set v2 radius profiles from M417 action-distance brackets and adds old-key spillover guards 9951 and 9939 before a no-PPO radius probe

## Next Blocker

m419-active-set-radius-anchor-export-implementation
