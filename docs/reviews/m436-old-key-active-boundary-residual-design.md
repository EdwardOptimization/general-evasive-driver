# m436-old-key-active-boundary-residual-design Research Review

## Summary

- Generated at UTC: 20260523T182746Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m437_active_boundary_residual_implementation
- Decision reason: M436 designs active-boundary preference residual for 10004 10023 and 9998 instead of more trajectory-radius tuning

## Hypothesis

An active-boundary residual using rejected-history preference or terminal-margin slack on 10004/10023/9998 will preserve old-key proof with less recovery-utility loss than full-trajectory action radii.

## Lineage

- parent_checkpoint: runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt, runs/m434_selective_10004_projection_r0015/candidate_checkpoint.pt, runs/m434_selective_10004_projection_r0020/candidate_checkpoint.pt
- parent_dataset: runs/m434_selective_10004_projection_summary, runs/m434_r0015_old_key_targeted_replay/guard_results.csv, runs/m434_r0020_old_key_targeted_replay/guard_results.csv, runs/m434_tail_r0010_old_key_targeted_replay/guard_results.csv
- parent_config: experiments/manifests/m435-selective-boundary-failure-audit.json
- parent_objective: active old-key boundary residual design
- derived_from: m435-selective-boundary-failure-audit
- blocked_by: m435-selective-boundary-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- specify active-boundary corpus fields
- specify loss terms and gate order
- state why the design is training-only and does not change deployable actor inputs
- admit an implementation milestone only if the design avoids more radius-only tuning

## Failure Criteria

- design still relies on broad full-trajectory action anchoring
- design requires differentiating through closed-loop replay without implementation plan
- design recommends PPO before proof residual implementation
- actor input or output contract changes

## Evidence Gates

- design only; no PPO
- active-boundary corpus specification for 10004 10023 9998
- next implementation must preserve actor input/output contract
- next probe must preserve exact M297/M270/old-key and replay gates

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

- milestone: m436-old-key-active-boundary-residual-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m437_active_boundary_residual_implementation
- reason: M436 designs active-boundary preference residual for 10004 10023 and 9998 instead of more trajectory-radius tuning

## Next Blocker

m437-active-boundary-residual-implementation
