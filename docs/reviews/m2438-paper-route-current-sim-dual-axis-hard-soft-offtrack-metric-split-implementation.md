# m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation Research Review

## Summary

- Generated at UTC: 20260602T194141Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_hard_soft_offtrack_metric_split_pass
- Decision reason: M2438 panel pass 12 rows 3 sources thresholds 0.02/0.05/0.10/0.20m actual success preserved guardrail 0 min soft gain at 0.20m 0.7175925925925926 no rollout repair training ranking verdict claims

## Hypothesis

A hard/soft offtrack metric split implementation will materialize M2437 semantics over existing episode rows while preserving actual success and keeping soft success diagnostic-only.

## Lineage

- parent_checkpoint: not_applicable_hard_soft_offtrack_metric_split_implementation
- parent_dataset: docs/m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design.md, runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/episode_rows.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv, runs/m2435_paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel/summary.json, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design.json
- parent_objective: materialize a hard/soft offtrack metric split classification panel over existing measured episode rows
- derived_from: m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design, m2362-paper-route-current-sim-dual-axis-repaired-pack-measured-execution, m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation, m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation, m2435-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-implementation
- blocked_by: M2437 must be implemented before measured rollout or training resumes, actual_success must remain an executed rollout outcome only, counterfactual soft success must stay diagnostic, hard/soft offtrack semantics must be materialized with guardrails before a result audit
- supersedes: direct measured rollout under ambiguous offtrack semantics, training/PPO before task-boundary metric split implementation, controller-family ranking before metric semantics are materialized
- invalidates: None

## Success Criteria

- runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json exists
- panel rows include M2362 M2397 and M2413 threshold rows
- thresholds 0.02 0.05 0.10 and 0.20 m are evaluated
- measured actual_success is preserved exactly
- hard offtrack soft offtrack collision-risk failure and boundary-tolerated diagnostic columns are generated
- the panel recommends a bounded non-ranking next route
- no rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2438 starts new measured rollout or reset rerun
- M2438 executes repair or training
- M2438 ranks candidate families or controllers
- M2438 treats soft success as actual success
- M2438 changes measured actual_success
- M2438 claims scenario redesign success
- M2438 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims
- M2438 omits required primary episode panels or thresholds

## Evidence Gates

- M2438 must read existing primary episode rows from M2362 M2397 and M2413
- M2438 must compute hard/soft/diagnostic offtrack columns for 0.02 0.05 0.10 and 0.20 m thresholds
- M2438 must preserve measured actual_success unchanged
- M2438 must keep counterfactual soft success separate from actual success
- M2438 must not run new rollout, execute repair, train, rank candidates/controllers, select winners, or make verdict claims

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

## Scoreboard

- milestone: m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation
- type: infrastructure
- checkpoint: runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_hard_soft_offtrack_metric_split_pass
- reason: M2438 panel pass 12 rows 3 sources thresholds 0.02/0.05/0.10/0.20m actual success preserved guardrail 0 min soft gain at 0.20m 0.7175925925925926 no rollout repair training ranking verdict claims

## Next Blocker

m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation
