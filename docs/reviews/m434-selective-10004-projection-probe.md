# m434-selective-10004-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T182241Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_primary_pass_admit_m435_selective_boundary_failure_audit
- Decision reason: M434 r0010 is proof-safe with recovery retained 0.1035 but below M427 and target while looser profiles fail old-key compact

## Hypothesis

One of the selective 10004 wrong-history guard profiles can recover more utility than M427 while preserving the exact and closed-loop proof gates restored by M430.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m433_selective_10004_anchor_export
- parent_config: experiments/manifests/m433-selective-10004-anchor-export.json
- parent_objective: no-PPO projected recovery with selective 10004 wrong-history guards
- derived_from: m433-selective-10004-anchor-export
- blocked_by: m433-selective-10004-anchor-export
- supersedes: None
- invalidates: None

## Success Criteria

- at least one profile passes exact M297/M270/old-key no-regression
- at least one exact-passing profile passes M267/M264 17/17 old-key compact 40/40 and M183/M170 17/17
- primary pass if a proof-passing profile reaches recovery retained vs M406 >= 0.20
- partial pass if a proof-passing profile exceeds M427 recovery retained 0.174354

## Failure Criteria

- all profiles fail exact gates
- all exact-passing profiles fail M267/M264 or old-key compact replay
- all proof-passing profiles stay at or below M430 recovery retained 0.061702
- actor input or output contract changes

## Evidence Gates

- exact M297 no-regression
- exact M270 no-regression
- old-key surrogate no-regression
- M267/M264 first replay 17/17
- old-key compact replay 40/40
- M183/M170 first replay 17/17
- recovery retained vs M406

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m434-selective-10004-projection-probe
- type: gate
- checkpoint: runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_primary_pass_admit_m435_selective_boundary_failure_audit
- reason: M434 r0010 is proof-safe with recovery retained 0.1035 but below M427 and target while looser profiles fail old-key compact

## Next Blocker

m435-selective-boundary-failure-audit
