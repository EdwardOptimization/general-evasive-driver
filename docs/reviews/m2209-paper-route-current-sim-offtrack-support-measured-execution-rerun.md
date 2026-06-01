# m2209-paper-route-current-sim-offtrack-support-measured-execution-rerun Research Review

## Summary

- Generated at UTC: 20260601T113308Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_offtrack_support_measured_execution_rerun_pass_route_to_result_audit
- Decision reason: M2209 repaired measured execution pass 2304 episodes 0 failures metadata 0 metric 0 guardrail 0 raw outcomes success 374 collision 49 offtrack 1881 no ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

After the M2207 metadata activation repair, the frozen 2304-cell current-sim offtrack-support measured execution can run without the M2204 pre-rollout metadata validation failure.

## Lineage

- parent_checkpoint: runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L0_current_masked/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L1_one_step/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_13/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_25/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_50/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L2_window_100/checkpoint.pt, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/checkpoints/L3_online_gru/checkpoint.pt
- parent_dataset: docs/m2208-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-result-audit.md, runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json, runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv
- parent_config: experiments/manifests/m2208-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-result-audit.json
- parent_objective: rerun repaired current-sim offtrack-support measured execution after metadata activation repair audit
- derived_from: m2208-paper-route-current-sim-measured-runner-repeat-metadata-activation-repair-result-audit
- blocked_by: M2208 must audit the repair before rerun
- supersedes: overwriting M2204 failed output directory
- invalidates: None

## Success Criteria

- runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json exists
- episode_count == 2304
- failure_count == 0
- spec_count == 288
- profile_count == 8
- metadata_missing_count == 0
- metric_completeness_failure_count == 0
- guardrail_violation_count == 0
- no ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- validation fails before rollout
- episode_count != 2304
- failure_count > 0
- metadata or metric completeness failures occur
- guardrail violations occur
- ranking or paper-level claims are made

## Evidence Gates

- M2209 must use the same M2194 repaired specs and M2200 materialized workload
- M2209 must write to a new rerun output directory
- M2209 must target 2304 episodes, 288 specs, and 8 profiles
- M2209 must not rank controller families or claim paper-level evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not change actor inputs
- do not change profile configs
- do not change task specs
- do not change materialized workload rows
- do not overwrite M2204 artifacts
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m2209-paper-route-current-sim-offtrack-support-measured-execution-rerun
- type: infrastructure
- checkpoint: runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json
- success_rate: 0.1623263888888889
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_offtrack_support_measured_execution_rerun_pass_route_to_result_audit
- reason: M2209 repaired measured execution pass 2304 episodes 0 failures metadata 0 metric 0 guardrail 0 raw outcomes success 374 collision 49 offtrack 1881 no ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2209-paper-route-current-sim-offtrack-support-measured-execution-rerun
