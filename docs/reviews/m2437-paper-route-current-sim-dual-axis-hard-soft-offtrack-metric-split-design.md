# m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design Research Review

## Summary

- Generated at UTC: 20260602T193202Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: hard_soft_offtrack_metric_split_design_route_to_implementation
- Decision reason: M2437 defines actual success collision-risk hard offtrack soft offtrack and boundary-tolerated diagnostic semantics then routes to implementation no rollout repair training ranking actual-success or verdict claims

## Hypothesis

A hard/soft offtrack metric split design will make the next current-sim validation route well-defined without leaking counterfactual soft success into actual success.

## Lineage

- parent_checkpoint: not_applicable_hard_soft_offtrack_metric_split_design
- parent_dataset: docs/m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit.md, runs/m2435_paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel/summary.json, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit.json
- parent_objective: design a hard/soft offtrack metric and termination split before any scenario redesign or measured rollout
- derived_from: m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit
- blocked_by: M2436 promotes to task-boundary metric/termination redesign branch, counterfactual soft success must not become actual success, hard/soft offtrack semantics must be specified before implementation
- supersedes: direct rollout under ambiguous offtrack semantics, training/PPO before metric split, controller-family comparison before task-boundary contract
- invalidates: None

## Success Criteria

- docs/m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design.md exists
- hard offtrack, soft offtrack, collision-risk failure, and actual success semantics are specified
- counterfactual soft success is explicitly barred from actual success
- implementation admission criteria are specified
- a bounded non-ranking next route is selected
- no rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2437 runs measured validation
- M2437 executes repair or training
- M2437 ranks candidate families or controllers
- M2437 treats soft success as actual success
- M2437 claims scenario redesign success
- M2437 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2437 must specify hard offtrack, soft offtrack, collision-risk failure, and actual success semantics
- M2437 must preserve that counterfactual relabeling is not actual success
- M2437 must define admission criteria for a future implementation/validation milestone
- M2437 must not run measured rollout, repair, train, rank candidates/controllers, select winners, or make verdict claims

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

- milestone: m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design
- type: infrastructure
- checkpoint: docs/m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hard_soft_offtrack_metric_split_design_route_to_implementation
- reason: M2437 defines actual success collision-risk hard offtrack soft offtrack and boundary-tolerated diagnostic semantics then routes to implementation no rollout repair training ranking actual-success or verdict claims

## Next Blocker

m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design
