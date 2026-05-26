# m953-v4-public-base-replay-constrained-target-feasibility-design Research Review

## Summary

- Generated at UTC: 20260526T003752Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: replay_constrained_target_feasibility_design_admit_m954
- Decision reason: M953 designs a no-training target-space audit with offline exact target metrics M267/M264 active-row closed-loop target preflight and joint feasibility route logic before any actor update

## Hypothesis

Before widening the actor or running more training, the project should prove that replay-constrained targets exist inside the current trust region.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m952-v4-public-base-controlled-fusion-branch-synthesis-2.md, runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/summary.json, runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/alpha_metrics.csv, runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/m267_preflight_summary.csv
- parent_config: experiments/manifests/m952-v4-public-base-controlled-fusion-branch-synthesis-2.json
- parent_objective: design a no-training feasibility audit for replay-constrained target construction before more actor updates
- derived_from: m952-v4-public-base-controlled-fusion-branch-synthesis-2
- blocked_by: controlled-fusion local objectives cannot produce exact/preflight overlap
- supersedes: None
- invalidates: additional local controlled-fusion coefficient retunes before target feasibility

## Success Criteria

- design document exists
- target feasibility criteria are explicit
- normal-retention, low-tail lift, and M267 proof constraints are all included
- next implementation route is specified
- training, PPO, and promotion remain blocked

## Failure Criteria

- design skips one of the three feasibility constraints
- design recommends training before feasibility
- design changes actor inputs
- design uses private holdout

## Evidence Gates

- M953 must not train
- M953 must not run PPO
- M953 must not promote
- M953 must preserve the P0 actor-input contract
- M953 must design a feasibility check for targets satisfying normal retention, low-tail lift, and M267 proof retention

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run another controlled-fusion local retune
- do not widen actor inputs
- do not open encoders or GRU
- do not use private holdout
- do not promote

## Failure Taxonomy

- none

## Scoreboard

- milestone: m953-v4-public-base-replay-constrained-target-feasibility-design
- type: infrastructure
- checkpoint: docs/m953-v4-public-base-replay-constrained-target-feasibility-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: replay_constrained_target_feasibility_design_admit_m954
- reason: M953 designs a no-training target-space audit with offline exact target metrics M267/M264 active-row closed-loop target preflight and joint feasibility route logic before any actor update

## Next Blocker

m954-v4-public-base-replay-constrained-target-feasibility-implementation
