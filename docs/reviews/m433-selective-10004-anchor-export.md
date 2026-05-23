# m433-selective-10004-anchor-export Research Review

## Summary

- Generated at UTC: 20260523T181619Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m434_selective_10004_projection_probe
- Decision reason: M433 exports six selective 10004 anchors and all no-update exact smokes pass

## Hypothesis

A profile exporter that selectively relaxes only 10004 wrong-history can create valid no-PPO probe anchors for testing proof-safe recovery utility without touching other guards.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m429_branch_split_old_key_guard/branch_split_hard_guard_anchor.npz
- parent_config: experiments/manifests/m432-selective-10004-guard-design.json
- parent_objective: selective 10004 wrong-history anchor profile export
- derived_from: m432-selective-10004-guard-design
- blocked_by: m432-selective-10004-guard-design
- supersedes: None
- invalidates: None

## Success Criteria

- all six profile anchors are exported with source metadata
- 10023 and 9872 guard sources remain unchanged
- 10004 wrong-history remains present in every profile
- no-update exact repair smoke passes for each profile

## Failure Criteria

- profile export corrupts trajectory anchor shapes
- 10004 wrong-history is removed completely
- no-update smoke regresses exact objectives
- actor input or output contract changes

## Evidence Gates

- export r0005 r0010 r0015 r0020 tail_r0005 tail_r0010 anchors
- no-update exact repair smoke for each anchor
- no actor input or output contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not remove 10004 wrong-history protection entirely
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m433-selective-10004-anchor-export
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m434_selective_10004_projection_probe
- reason: M433 exports six selective 10004 anchors and all no-update exact smokes pass

## Next Blocker

m434-selective-10004-projection-probe
