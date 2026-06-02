# m2447-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization Research Review

## Summary

- Generated at UTC: 20260602T211734Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: M2447 localization pass 65 rows global hard_offtrack_rate 0.7468571428571429 top diagnostic slices off_track centerline drift_required early_far no rerun repair training ranking verdict claims
- Decision reason: M2447 passes if it localizes M2445 outcomes into diagnostic non-ranking slices and selects a bounded route without rerun, repair, training, ranking, winner selection, or verdict claims.

## Hypothesis

M2445 hard-offtrack dominance can be localized into diagnostic slices from artifacts only, enabling a bounded next route without rerun, repair, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_localization
- parent_dataset: docs/m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit.md, runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/summary.json, runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/episode_rows.csv, runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/episode_family_membership_rows.csv, runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/aggregate_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit.json
- parent_objective: localize hard-offtrack-dominated M2445 measured outcome without rerun or repair
- derived_from: m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit, m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation
- blocked_by: M2446 accepted M2445 but found hard-offtrack-dominated measured outcome, next route needs localization before any repair/training/scenario-quality decision
- supersedes: direct repair/training after M2445, ranking candidate or controller axes from diagnostic aggregates
- invalidates: None

## Success Criteria

- runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/summary.json exists
- localization rows cover M2445 hard offtrack, collision, soft violation, and success outcomes
- diagnostic axes remain non-ranking and winner_selected false
- a bounded non-ranking next route is selected or the route is stopped
- no rerun repair training ranking actual-success-improvement or verdict claim is made

## Failure Criteria

- M2447 reruns measured validation or policy action
- M2447 executes repair or training
- M2447 ranks candidate families, controller families, or selected checkpoints
- M2447 selects a winner
- M2447 makes current-sim, paper, FW-vs-GRU, self-ID, scenario-redesign, or training-repair verdict claims

## Evidence Gates

- M2447 must use only M2445 artifacts and must not rerun measured rollout
- M2447 must localize hard offtrack, collision, soft violation, and success rows across diagnostic axes
- M2447 must preserve candidate/profile/family/controller axes as diagnostic-only and non-ranking
- M2447 must write localization rows, guardrail rows, summary, and decision rows
- M2447 must choose bounded next route or stop without repair, training, ranking, winner selection, or verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun measured policy rollout
- do not execute policy action
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not overwrite active configs
- do not change actor inputs
- do not inject hidden or oracle actor features
- do not rank candidate families
- do not rank controller families
- do not rank selected checkpoints
- do not select a winner
- do not claim actual success improvement
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2447-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization
- type: infrastructure
- checkpoint: runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/summary.json
- success_rate: 0.06685714285714285
- termination_rate: None
- clearance_margin_mean: 6.847753455149411
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: current_sim_dual_axis_metric_selected_measured_validation_outcome_localization_pass
- decision: M2447 localization pass 65 rows global hard_offtrack_rate 0.7468571428571429 top diagnostic slices off_track centerline drift_required early_far no rerun repair training ranking verdict claims
- reason: None

## Next Blocker

m2447-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization
