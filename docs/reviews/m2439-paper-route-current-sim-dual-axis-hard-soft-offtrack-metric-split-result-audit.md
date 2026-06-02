# m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit Research Review

## Summary

- Generated at UTC: 20260602T194929Z
- Type: gate
- Gate tier: process
- Promotion decision: accept_metric_split_route_to_metric_selected_measured_validation_design
- Decision reason: M2439 accepts M2438 metric split implementation and routes to metric-selected measured-validation design while keeping soft success diagnostic-only no rollout repair training ranking verdict claims

## Hypothesis

Auditing M2438 will determine whether the hard/soft offtrack split is ready for a bounded metric-selected measured-validation design without leaking soft success into actual success.

## Lineage

- parent_checkpoint: not_applicable_hard_soft_offtrack_metric_split_result_audit
- parent_dataset: docs/m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation.md, runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json, runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/panel_rows.csv, runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/decision_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation.json
- parent_objective: audit the hard/soft offtrack metric split panel and choose a bounded next route
- derived_from: m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation
- blocked_by: M2438 must be audited before measured validation or training, counterfactual soft success remains diagnostic-only, current-sim verdict requires a later executed metric-selected validation
- supersedes: direct rollout after metric split without audit, training/PPO before metric split audit, controller-family ranking from diagnostic soft success
- invalidates: None

## Success Criteria

- docs/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.md exists
- M2438 summary panel and decision rows are audited
- counterfactual soft success is kept separate from actual success
- a bounded non-ranking next route is selected or the route is stopped
- no rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2439 reruns measured validation
- M2439 executes repair or training
- M2439 ranks candidate families or controllers
- M2439 treats soft success as actual success
- M2439 claims scenario redesign success
- M2439 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2439 must audit M2438 summary panel and decision rows
- M2439 must preserve that counterfactual soft success is not actual success
- M2439 must choose a bounded next route or stop
- M2439 must not rerun measured rollout, repair, train, rank candidates/controllers, select winners, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run new measured rollout
- do not rerun reset
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

## Scoreboard

- milestone: m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit
- type: gate
- checkpoint: docs/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: accept_metric_split_route_to_metric_selected_measured_validation_design
- reason: M2439 accepts M2438 metric split implementation and routes to metric-selected measured-validation design while keeping soft success diagnostic-only no rollout repair training ranking verdict claims

## Next Blocker

m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit
