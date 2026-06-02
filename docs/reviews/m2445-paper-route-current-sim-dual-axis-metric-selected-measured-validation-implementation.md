# m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation Research Review

## Summary

- Generated at UTC: 20260602T210534Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: M2445 measured-validation artifact pass 5250/5250 episodes failures 0 hard_offtrack_failure_rate 0.7468571428571429 soft_violation_rate 0.0032380952380952383 no repair training ranking winner verdict claims
- Decision reason: M2445 passes if it executes or fail-closes the audited metric-selected measured-validation workload and routes to result audit without repair, training, ranking, winner selection, or verdict claims.

## Hypothesis

The audited M2443 workload can be executed as a bounded metric-selected measured validation under soft-boundary task metrics without repair, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: M2262 selected checkpoint set from selected_checkpoint_rows.csv
- parent_dataset: docs/m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit.md, runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/workload_rows.csv, runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/soft_reset_target_rows.csv, runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/reset_validation_rows.csv, runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/summary.json, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit.json, experiments/manifests/m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation.json
- parent_objective: execute bounded metric-selected measured validation under the audited soft-boundary workload
- derived_from: m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit, m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation, m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design
- blocked_by: fresh executed metric-selected measured validation has not yet been run, current-sim verdict requires later result audit after executed rows exist
- supersedes: old-row relabel panels as substitute for fresh metric-selected execution, reset-only preflight as substitute for measured driving evidence
- invalidates: None

## Success Criteria

- runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/summary.json exists
- episode rows cover the M2443 350 x 15 denominator or fail closed with explicit coverage gaps
- soft-boundary hard/soft task metrics are recorded
- actor input contract is preserved
- repair/training/ranking/winner/verdict guardrails remain zero
- a bounded result-audit route is selected

## Failure Criteria

- M2445 executes repair or training
- M2445 ranks candidate families or controllers
- M2445 selects a winner or promotes a checkpoint
- M2445 changes actor input contract
- M2445 makes current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2445 must use M2443 workload/preflight artifacts as the executed denominator
- M2445 must execute exactly 350 reset targets x 15 selected checkpoints unless it fails closed with explicit gaps
- M2445 must enable soft_offtrack_metric_enabled true and soft_offtrack_tolerance_m 0.20
- M2445 must preserve actor inputs and avoid hidden/oracle feature injection
- M2445 must write episode rows, aggregate metrics, validation failures, and decision rows
- M2445 must not execute repair, train, replay/PPO, rank candidates/controllers, select winners, promote checkpoints, or make paper/current-sim/self-ID verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not execute repair levers
- do not train
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not overwrite active configs
- do not change actor inputs
- do not inject hidden or oracle actor features
- do not rank candidate families
- do not rank controller families
- do not select a winner
- do not claim actual success improvement before result audit
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
- training_instability

## Scoreboard

- milestone: m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation
- type: infrastructure
- checkpoint: runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/summary.json
- success_rate: 0.06685714285714285
- termination_rate: None
- clearance_margin_mean: 6.847753455149411
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: current_sim_dual_axis_metric_selected_measured_validation_pass
- decision: M2445 measured-validation artifact pass 5250/5250 episodes failures 0 hard_offtrack_failure_rate 0.7468571428571429 soft_violation_rate 0.0032380952380952383 no repair training ranking winner verdict claims
- reason: None

## Next Blocker

m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation
