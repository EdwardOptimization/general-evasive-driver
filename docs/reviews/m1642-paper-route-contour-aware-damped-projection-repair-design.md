# m1642-paper-route-contour-aware-damped-projection-repair-design Research Review

## Summary

- Generated at UTC: 20260529T202040Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_damped_projection_design_admit_bounded_implementation
- Decision reason: M1642 pre-registers a normalized full-batch damped backtracking projection rule and admits one no-checkpoint implementation before mandatory audit

## Hypothesis

A deterministic damped/backtracking projection design can address M1640 optimizer-step instability while preserving exact-objective role guardrails.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1641-paper-route-contour-aware-exact-objective-projection-repair-result-audit.md, runs/m1640_contour_aware_exact_objective_projection_repair/summary.json, runs/m1640_contour_aware_exact_objective_projection_repair/optimization_trace.csv
- parent_config: experiments/manifests/m1641-paper-route-contour-aware-exact-objective-projection-repair-result-audit.json
- parent_objective: design damped/backtracking exact-objective projection repair after M1640 optimizer-step instability
- derived_from: m1641-paper-route-contour-aware-exact-objective-projection-repair-result-audit
- blocked_by: M1640 Adam lr=1e-3 projection overshot the controlled scale_1e-3 perturbation and did not reduce exact residual
- supersedes: rerunning M1640 with ad hoc learning-rate tuning, direct checkpoint artifact after M1641, direct PPO after M1641, direct promotion after M1641
- invalidates: None

## Success Criteria

- docs/m1642-paper-route-contour-aware-damped-projection-repair-design.md exists
- design specifies actor_mean-only gradient scope
- design specifies full-batch exact objective and diagnostic zero-weight policy
- design specifies deterministic damping/backtracking candidate selection
- design specifies residual and trust-region acceptance criteria
- design keeps checkpoint artifacts PPO promotion private holdout actor-input changes and level3 claims blocked

## Failure Criteria

- design document is missing
- design admits ad hoc learning-rate search without pre-registered selection
- design lets diagnostics or donor-plus actions enter the loss target
- design routes directly to checkpoint artifact PPO promotion private holdout or actor-input changes
- design claims paper-level or level3 self-identification evidence

## Evidence Gates

- M1642 must design a damped/backtracking projection repair before any rerun
- M1642 must keep optimization scope to actor_mean.weight and actor_mean.bias
- M1642 must keep diagnostics zero-weight and donor-plus actions excluded from loss
- M1642 must pre-register trust-region and exact-residual acceptance rules
- M1642 must keep checkpoint artifacts PPO promotion private holdout and actor-input changes blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run projection
- do not train
- do not run PPO
- do not run closed-loop evaluation
- do not write checkpoint artifacts
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not treat donor_plus_hidden_action as a loss target
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1642-paper-route-contour-aware-damped-projection-repair-design
- type: gate
- checkpoint: docs/m1642-paper-route-contour-aware-damped-projection-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_damped_projection_design_admit_bounded_implementation
- reason: M1642 pre-registers a normalized full-batch damped backtracking projection rule and admits one no-checkpoint implementation before mandatory audit

## Next Blocker

m1643-paper-route-contour-aware-damped-projection-repair-implementation
