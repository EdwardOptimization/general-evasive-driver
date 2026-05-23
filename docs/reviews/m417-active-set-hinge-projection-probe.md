# m417-active-set-hinge-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T165226Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_active_set_hinge_candidate_admit_m418_radius_calibration_design
- Decision reason: M417 shows a hard proof/utility switch: lambda 1e12 retains 22.6 percent recovery utility but fails M267/M264 and old-key proof; lambda 1e13 passes first proof gates but retains only 5.4 percent recovery utility

## Hypothesis

An active-set hinge anchor can repair M414 proof failures while retaining at least 20% of the M406 recovery movement.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m416_active_set_hinge_anchor/active_set_hinge_trajectory_anchor.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
- parent_config: experiments/manifests/m416-active-set-hinge-anchor-implementation.json
- parent_objective: probe active-set hinge replay residual without PPO
- derived_from: m416-active-set-hinge-anchor-implementation
- blocked_by: m414-source-weighted-replay-anchor-probe
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes exact M297/M270/old-key no-regression
- candidate passes M267/M264 first replay with 17/17 success drops
- candidate passes old-key compact replay with 0 accepted regressions
- candidate passes M183/M170 first replay with 17/17 success drops
- candidate retains at least 20% of M406 recovery improvement

## Failure Criteria

- exact gates regress
- M267/M264 or old-key proof gates fail
- candidate passes proof but recovery-retention ratio is below 0.20
- actor input or output contract changes

## Evidence Gates

- exact M297 no-regression
- exact M270 no-regression
- old-key surrogate no-regression
- M267/M264 first replay
- old-key compact replay
- M183/M170 first replay if first gates pass
- recovery improvement retained vs M406 >= 0.20

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- objective_overfit
- promotion_gate_failure

## Scoreboard

- milestone: m417-active-set-hinge-projection-probe
- type: gate
- checkpoint: runs/m417_active_set_hinge_projection_ltraj1e13_s40_seed10148/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_active_set_hinge_candidate_admit_m418_radius_calibration_design
- reason: M417 shows a hard proof/utility switch: lambda 1e12 retains 22.6 percent recovery utility but fails M267/M264 and old-key proof; lambda 1e13 passes first proof gates but retains only 5.4 percent recovery utility

## Next Blocker

m418-active-set-radius-calibration-design
