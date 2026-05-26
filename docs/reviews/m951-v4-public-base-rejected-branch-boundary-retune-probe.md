# m951-v4-public-base-rejected-branch-boundary-retune-probe Research Review

## Summary

- Generated at UTC: 20260526T002724Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: rejected_branch_boundary_retune_objective_conflict_route_to_branch_synthesis
- Decision reason: M951 improves M267 preflight to 13 pass alphas but exact_candidate_alpha_count remains 0 so local retuning is exhausted and branch synthesis is required

## Hypothesis

Training the rejected-branch retention objective at lower boundary alphas may create overlap between exact low-tail compatibility and M267/M264 preflight.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m950-v4-public-base-rejected-branch-retention-objective-conflict-audit.md, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/summary.json, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/alpha_metrics.csv, runs/m949_v4_public_base_controlled_fusion_rejected_branch_retention_probe/m267_preflight_summary.csv
- parent_config: experiments/manifests/m950-v4-public-base-rejected-branch-retention-objective-conflict-audit.json
- parent_objective: run one bounded lower-boundary retune of the rejected-branch retention objective
- derived_from: m950-v4-public-base-rejected-branch-retention-objective-conflict-audit
- blocked_by: M949 has no overlap between exact low-tail candidate and M267/M264 preflight
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- loss coefficients are recorded
- train_alphas include 0.0675, 0.0750, 0.0900, and 0.1000
- exact metrics and M267 preflight are evaluated
- candidate_alpha_count is reported
- ppo_used and promoted are false

## Failure Criteria

- actor inputs change
- forbidden parameters change
- M267/M264 preflight is skipped
- PPO or promotion is run
- a second local retune is recommended without synthesis

## Evidence Gates

- M951 must preserve the P0 actor-input contract
- M951 may train only actor_mean and response_context_fusion.0
- M951 must use lower boundary train alphas
- M951 must evaluate exact metrics and M267/M264 preflight
- M951 must not run PPO
- M951 must not promote

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run another local coefficient tweak after M951 without synthesis
- do not open encoders or GRU
- do not widen actor inputs
- do not full-replay a non-candidate
- do not run PPO or promotion

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m951-v4-public-base-rejected-branch-boundary-retune-probe
- type: infrastructure
- checkpoint: runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: rejected_branch_boundary_retune_objective_conflict_route_to_branch_synthesis
- reason: M951 improves M267 preflight to 13 pass alphas but exact_candidate_alpha_count remains 0 so local retuning is exhausted and branch synthesis is required

## Next Blocker

m952-v4-public-base-controlled-fusion-branch-synthesis-2
