# m435-selective-boundary-failure-audit Research Review

## Summary

- Generated at UTC: 20260523T182522Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m436_old_key_active_boundary_residual_design
- Decision reason: M435 finds selective radius is bounded by multi-key old-key boundary 10023 then 10004 and 9998

## Hypothesis

M434's selective radius family is limited by a multi-key old-key boundary, not only by 10004; the next useful residual should target terminal margin or rejected-branch preference rather than more radius tuning.

## Lineage

- parent_checkpoint: runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt, runs/m434_selective_10004_projection_r0015/candidate_checkpoint.pt, runs/m434_selective_10004_projection_tail_r0010/candidate_checkpoint.pt
- parent_dataset: runs/m434_selective_10004_projection_summary, runs/m434_r0015_old_key_targeted_replay/guard_results.csv, runs/m434_r0020_old_key_targeted_replay/guard_results.csv, runs/m434_tail_r0010_old_key_targeted_replay/guard_results.csv
- parent_config: experiments/manifests/m434-selective-10004-projection-probe.json
- parent_objective: audit selective-radius proof/utility boundary
- derived_from: m434-selective-10004-projection-probe
- blocked_by: m434-selective-10004-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- attribute which old-key rows become active as 10004 is relaxed
- explain why r0010 is proof-safe but below the utility target
- decide whether to design terminal-margin/rejected-branch residuals or another radius export
- do not claim a promoted base

## Failure Criteria

- cannot identify the active boundary rows
- audit recommends PPO before proof residual redesign
- audit relies on lowered thresholds
- actor input or output contract changes

## Evidence Gates

- old-key failure row attribution for r0015 r0020 tail profiles
- proof-safe utility ceiling comparison against M430 M427 and target 0.20
- next residual design recommendation without PPO

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

- milestone: m435-selective-boundary-failure-audit
- type: gate
- checkpoint: runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m436_old_key_active_boundary_residual_design
- reason: M435 finds selective radius is bounded by multi-key old-key boundary 10023 then 10004 and 9998

## Next Blocker

m436-old-key-active-boundary-residual-design
