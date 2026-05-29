# m1632-paper-route-contour-aware-policy-target-objective-design Research Review

## Summary

- Generated at UTC: 20260529T193515Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_policy_target_objective_design_admit_exact_evaluator
- Decision reason: M1632 designs role-safe correct/wrong hidden action residual objective semantics and admits one no-update exact evaluator implementation

## Hypothesis

The M1630 materialized positive and diagnostic tensor bundles are sufficient to design a role-safe contour-aware policy-target objective.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1630_contour_aware_full_target_materialization/summary.json, docs/m1631-paper-route-contour-aware-full-target-materialization-result-audit.md, docs/m1630-paper-route-contour-aware-full-target-materialization-implementation.md
- parent_config: experiments/manifests/m1631-paper-route-contour-aware-full-target-materialization-result-audit.json
- parent_objective: design objective semantics over materialized contour-aware policy targets
- derived_from: m1631-paper-route-contour-aware-full-target-materialization-result-audit
- blocked_by: M1631 admits design-only objective planning and blocks implementation/training
- supersedes: direct loss implementation from M1630, direct actor update from M1630, direct PPO after M1630
- invalidates: None

## Success Criteria

- docs/m1632-paper-route-contour-aware-policy-target-objective-design.md exists
- design defines positive-target terms and diagnostic guardrail terms separately
- design defines exact-evaluator criteria before actor update
- design states supported and unsupported claims
- training PPO promotion and private holdout remain blocked

## Failure Criteria

- design document is missing
- design treats diagnostics as positive targets
- design requires new actor inputs or oracle labels
- design routes directly to training PPO promotion private holdout or actor-input changes
- design claims paper-level or level3 self-identification evidence

## Evidence Gates

- M1632 must design objective semantics only
- M1632 must keep positives and diagnostics role-separated
- M1632 must define guardrails that prevent diagnostics from becoming positive targets
- M1632 must define exact-evaluator admission criteria before any actor update
- M1632 must keep training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not implement a loss
- do not construct an objective config artifact
- do not train
- do not run PPO
- do not run actor update
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not treat diagnostics as positive targets
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1632-paper-route-contour-aware-policy-target-objective-design
- type: gate
- checkpoint: docs/m1632-paper-route-contour-aware-policy-target-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_policy_target_objective_design_admit_exact_evaluator
- reason: M1632 designs role-safe correct/wrong hidden action residual objective semantics and admits one no-update exact evaluator implementation

## Next Blocker

m1632-paper-route-contour-aware-policy-target-objective-design
