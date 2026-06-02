# m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design Research Review

## Summary

- Generated at UTC: 20260602T195426Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: metric_selected_validation_protocol_route_to_soft_boundary_env_support
- Decision reason: M2440 designs fresh metric-selected validation protocol and routes to opt-in soft-boundary env support because current offtrack termination is hard-coded no rollout repair training ranking verdict claims

## Hypothesis

A metric-selected measured-validation design will define how to obtain executed rollout evidence under the hard/soft offtrack metric without conflating old-row soft success with actual success.

## Lineage

- parent_checkpoint: not_applicable_metric_selected_measured_validation_design
- parent_dataset: docs/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.md, docs/m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation.md, runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.json
- parent_objective: design a fresh measured-validation protocol under the hard/soft offtrack metric
- derived_from: m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit
- blocked_by: fresh measured validation must be designed before actual success can be claimed under the hard/soft metric, counterfactual relabeling is not actual success, metric-selected validation must preserve obstacle-risk and hard-failure reporting
- supersedes: direct measured rollout without protocol, training/PPO before metric-selected measured validation, current-sim verdict from old-row relabeling
- invalidates: None

## Success Criteria

- docs/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.md exists
- threshold policy source scenarios checkpoint set hard failure soft violation and guardrail reporting are specified
- actual success remains an executed rollout outcome only
- a bounded non-ranking next route is selected
- no rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2440 starts measured validation
- M2440 executes repair or training
- M2440 ranks candidate families or controllers
- M2440 treats old soft success as actual success
- M2440 claims scenario redesign success
- M2440 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2440 must design a metric-selected measured-validation protocol
- M2440 must preserve actual success as an executed rollout outcome
- M2440 must specify threshold policy, source scenarios, checkpoint set, hard failure, soft violation, and guardrail reporting
- M2440 must not run measured rollout, repair, train, rank candidates/controllers, select winners, or make verdict claims

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

- milestone: m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design
- type: infrastructure
- checkpoint: docs/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: metric_selected_validation_protocol_route_to_soft_boundary_env_support
- reason: M2440 designs fresh metric-selected validation protocol and routes to opt-in soft-boundary env support because current offtrack termination is hard-coded no rollout repair training ranking verdict claims

## Next Blocker

m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design
