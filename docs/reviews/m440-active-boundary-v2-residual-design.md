# m440-active-boundary-v2-residual-design Research Review

## Summary

- Generated at UTC: 20260523T185630Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m441_active_boundary_v2_residual_implementation
- Decision reason: M440 designs active-boundary v2 with active-case trajectory windows row-specific wrong/gap residuals and normal-safety guards before any projection

## Hypothesis

A v2 active-boundary residual should use row-specific trajectory-window and normal-safety terms rather than a stronger scalar one-step active-boundary loss.

## Lineage

- parent_checkpoint: runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt
- parent_dataset: runs/m439_active_boundary_residual_utility_audit/policy_utility_summary.csv, runs/m439_active_boundary_residual_utility_audit/active_case_rows.csv, runs/m437_active_boundary_residual/active_boundary_corpus.npz
- parent_config: experiments/manifests/m439-active-boundary-residual-utility-audit.json
- parent_objective: active-boundary v2 residual design
- derived_from: m439-active-boundary-residual-utility-audit
- blocked_by: m439-active-boundary-residual-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- specify whether active-boundary v2 is worth implementing
- define corpus fields for trajectory-window or margin-slack active cases
- define separate terms for 10004/9998 wrong-history safety and 10023 gap erosion
- state gate order and stop conditions before another projection

## Failure Criteria

- design is just another scalar weight sweep
- design becomes broad full-trajectory imitation without row-level justification
- design recommends PPO before proof residual implementation
- actor input or output contract changes

## Evidence Gates

- design only; no PPO
- active-case trajectory-window or margin-slack corpus specification
- normal-safety guard for high active-boundary pressure
- next implementation must preserve actor input/output contract

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

- milestone: m440-active-boundary-v2-residual-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m441_active_boundary_v2_residual_implementation
- reason: M440 designs active-boundary v2 with active-case trajectory windows row-specific wrong/gap residuals and normal-safety guards before any projection

## Next Blocker

m441-active-boundary-v2-residual-implementation
