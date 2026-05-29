# m1621-paper-route-contour-aware-policy-target-materialization-design Research Review

## Summary

- Generated at UTC: 20260529T184147Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_policy_target_materialization_design_admit_audit
- Decision reason: M1621 designs traceable policy-side target materialization and tensor-capture rerun requirements before implementation

## Hypothesis

A design-only materialization plan can specify how to convert contour-aware candidate rows into policy-side target artifacts before any optimizer is built.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv, runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv, runs/m1619_contour_aware_candidate_objective_evaluator/summary.json, docs/m1620-paper-route-contour-aware-candidate-objective-evaluator-result-audit.md
- parent_config: experiments/manifests/m1620-paper-route-contour-aware-candidate-objective-evaluator-result-audit.json
- parent_objective: design policy-side target materialization before any objective update
- derived_from: m1620-paper-route-contour-aware-candidate-objective-evaluator-result-audit
- blocked_by: M1620 finds the evaluator residual finite but metadata/row-metric only; policy-side target materialization is required before objective update
- supersedes: direct objective-only update from M1619, direct actor update from M1619, direct PPO after M1619
- invalidates: None

## Success Criteria

- docs/m1621-paper-route-contour-aware-policy-target-materialization-design.md exists
- source traceability from M1615 rows is explicit
- positive target schema is explicit
- diagnostic guardrail schema is explicit
- audit-before-implementation route is explicit
- implementation objective update training PPO promotion private holdout and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design skips source traceability
- design treats diagnostics as positive targets
- design routes directly to objective update training PPO promotion private holdout or actor-input changes

## Evidence Gates

- M1621 must design policy-side target materialization without implementing it
- M1621 must specify traceability from M1615 candidate rows to source artifacts
- M1621 must keep positive targets and diagnostic guardrails separated
- M1621 must require audit before implementation
- M1621 must keep objective update training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not implement materialization
- do not construct a loss
- do not construct an objective config
- do not train
- do not run PPO
- do not run actor update
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not claim level3 self-identification
- do not treat diagnostic guardrails as positive rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1621-paper-route-contour-aware-policy-target-materialization-design
- type: gate
- checkpoint: docs/m1621-paper-route-contour-aware-policy-target-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_policy_target_materialization_design_admit_audit
- reason: M1621 designs traceable policy-side target materialization and tensor-capture rerun requirements before implementation

## Next Blocker

m1622-paper-route-contour-aware-policy-target-materialization-design-audit
