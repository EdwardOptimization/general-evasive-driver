# m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation Research Review

## Summary

- Generated at UTC: 20260602T202735Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: current_sim_dual_axis_metric_selected_validation_preflight_pass
- Decision reason: M2443 preflight pass workload 5250 reset targets 350 selected checkpoints 15 source cells 5250 missing 0 duplicate 0 reset success 350 observation shape changed 0 policy action 0 guardrail 0 no rollout repair training ranking verdict claims

## Hypothesis

A metric-selected validation preflight can materialize and reset-test the M2413 denominator under soft-boundary config without running policy rollout.

## Lineage

- parent_checkpoint: not_applicable_metric_selected_validation_preflight
- parent_dataset: docs/m2442-paper-route-current-sim-dual-axis-task-boundary-metric-redesign-branch-synthesis.md, docs/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.md, docs/m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation.md, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2442-paper-route-current-sim-dual-axis-task-boundary-metric-redesign-branch-synthesis.json
- parent_objective: materialize a metric-selected validation preflight over the M2413 reset target set without policy rollout
- derived_from: m2442-paper-route-current-sim-dual-axis-task-boundary-metric-redesign-branch-synthesis, m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation, m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation
- blocked_by: fresh measured validation needs workload/reset preflight under soft-boundary env config, actual success cannot be claimed until executed rollout, M2442 synthesis requires fresh preflight evidence before another same-data audit
- supersedes: direct full measured rollout without preflight, another old-row relabel panel, training/PPO before metric-selected validation evidence
- invalidates: None

## Success Criteria

- runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/summary.json exists
- workload rows cover the M2413 350 x 15 denominator or fail closed with explicit coverage gaps
- soft-boundary env configs build and reset
- actor observation shape is unchanged
- policy action count is zero
- a bounded non-ranking next route is selected
- no measured policy rollout repair training ranking actual-success or verdict claim is made

## Failure Criteria

- M2443 executes policy action or measured policy rollout
- M2443 executes repair or training
- M2443 ranks candidate families or controllers
- M2443 treats preflight reset as actual success
- M2443 changes actor input contract
- M2443 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2443 must materialize metric-selected workload/preflight artifacts from M2413 lineage
- M2443 must use soft_offtrack_metric_enabled true and soft_offtrack_tolerance_m 0.20 in generated env configs
- M2443 must validate config build/reset and actor observation shape without policy action
- M2443 must not run measured policy rollout, repair, train, rank candidates/controllers, select winners, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run measured policy rollout
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

- milestone: m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation
- type: infrastructure
- checkpoint: runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_dual_axis_metric_selected_validation_preflight_pass
- reason: M2443 preflight pass workload 5250 reset targets 350 selected checkpoints 15 source cells 5250 missing 0 duplicate 0 reset success 350 observation shape changed 0 policy action 0 guardrail 0 no rollout repair training ranking verdict claims

## Next Blocker

m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation
