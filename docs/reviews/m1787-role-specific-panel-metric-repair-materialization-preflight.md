# m1787-role-specific-panel-metric-repair-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260530T082739Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: role_specific_panel_metric_repair_materialization_pass_route_to_result_audit
- Decision reason: M1787 materializes six v2 role surfaces 276 matrix rows ranking blocked by default preserved profile controls and zero guardrail violations

## Hypothesis

The M1786 repair design can be materialized into complete v2 role-specific panel and metric contract artifacts without running reset or rollout.

## Lineage

- parent_checkpoint: not_applicable_no_rollout_materialization_preflight
- parent_dataset: docs/m1786-role-specific-panel-metric-repair-design.md, docs/m1785-role-specific-scorecard-blocker-localization.md, runs/m1783_role_specific_metric_scorecard_extraction/metric_contract.csv, runs/m1783_role_specific_metric_scorecard_extraction/ranking_blockers.csv
- parent_config: experiments/manifests/m1786-role-specific-panel-metric-repair-design.json
- parent_objective: materialize v2 role-specific panel and metric repair contract without rollout
- derived_from: m1786-role-specific-panel-metric-repair-design
- blocked_by: M1786 admits v2 no-rollout materialization preflight before reset or measured execution
- supersedes: running reset feasibility or measured execution on unrepaired scorecard semantics
- invalidates: None

## Success Criteria

- runs/m1787_role_specific_panel_metric_repair_materialization_preflight/summary.json exists
- all v2 contract artifacts from M1786 exist
- role_surface_count >= 4
- ranking_admissible_by_default == false
- mitigation uses impact severity rather than obstacle-pass success as primary metric
- profile controls are preserved
- guardrail_violation_count == 0

## Failure Criteria

- required artifacts are missing
- materialization reruns reset or rollout
- ranking is admitted by default
- profile controls are lost
- mitigation uses obstacle-pass success as primary metric
- next route is ambiguous

## Evidence Gates

- M1787 must materialize the v2 role surface metric and admissibility contract without reset or rollout
- M1787 must write summary role_surface_contract metric_contract_v2 admissibility_contract panel_repair_specs panel_repair_matrix metric_only_repair_plan new_materialization_required and claim_boundary artifacts
- M1787 must preserve profile controls and keep ranking_admissible_by_default false
- M1787 must not train replay PPO promote use private holdout change actor inputs tune profiles rank controller families or claim paper-level evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact
- behavior_regression

## Scoreboard

- milestone: m1787-role-specific-panel-metric-repair-materialization-preflight
- type: infrastructure
- checkpoint: runs/m1787_role_specific_panel_metric_repair_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: role_specific_panel_metric_repair_materialization_pass_route_to_result_audit
- reason: M1787 materializes six v2 role surfaces 276 matrix rows ranking blocked by default preserved profile controls and zero guardrail violations

## Next Blocker

m1788-role-specific-panel-metric-repair-materialization-result-audit
