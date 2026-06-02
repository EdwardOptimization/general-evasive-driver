# m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation Research Review

## Summary

- Generated at UTC: 20260602T143348Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_linked_measured_validation_pass_route_to_result_audit
- Decision reason: M2413 completes 5250/5250 source-linked measured episodes reset targets 350 selected 15 family membership rows 18300 failure/validation/metadata/metric/contract/guardrail 0 outcome offtrack-dominated offtrack_rate 0.7424761904761905 no ranking/verdict claims

## Hypothesis

The M2410 reset panel can be measured as 5250 closed-loop episodes while preserving actor contract, family-overlap diagnostics, and non-ranking claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_measured_validation_uses_selected_public_checkpoints
- parent_dataset: docs/m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design.md, runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json, runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/reset_target_rows.csv, runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/source_linked_family_rows.csv, runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/source_linked_scenario_rows.csv, runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/unmatched_source_key_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_config_rows.csv, runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization/effective_candidate_configs/*.json, runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv, runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs
- parent_config: experiments/manifests/m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design.json
- parent_objective: implement and run the bounded 350 reset target x 15 selected checkpoint source-linked measured-validation panel
- derived_from: m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design, m2410-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-implementation
- blocked_by: M2412 design is required before measured execution, family membership is overlapping and must remain diagnostic, unmatched source-key diagnostics must be preserved
- supersedes: using 3505 source-linked scenario refs as independent rollout units, family ranking from overlapping membership, current-sim verdict from reset-only evidence
- invalidates: None

## Success Criteria

- runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json exists
- result_class is current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass
- source_reset_target_count is 350
- selected_checkpoint_count is 15
- episode_count is 5250
- failure_count is 0
- validation_failure_count is 0
- metadata_missing_count is 0
- metric_completeness_failure_count is 0
- actor_contract_violation_count is 0
- guardrail_violation_count is 0
- ranking_admissible_count and winner_selected_count are 0
- episode_family_membership_rows.csv exists and preserves overlapping family membership

## Failure Criteria

- episode count is incomplete
- validation failures or rollout failures occur
- metadata or metric completeness fails
- actor contract validation fails
- family membership is collapsed into ranking
- repair execution training replay PPO ranking or winner selection occurs
- M2413 claims measured driver success, paper verdict, current-sim verdict, scenario redesign executed, training repair success, FW-vs-GRU conclusion, or level3 self-ID

## Evidence Gates

- M2413 must execute exactly 5250 measured episodes if validation passes
- M2413 must use 350 unique reset targets and 15 selected checkpoints
- M2413 must write one primary episode row per reset_target_key plus selected_checkpoint workload
- M2413 must write exploded family-membership diagnostic rows separately
- M2413 must preserve P0 human-view no-wheel no-oracle actor contract
- M2413 must preserve the 95 unmatched source-key diagnostic caveat
- M2413 must not execute repair, train, replay, PPO, rank families/profiles/controllers, select winner, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

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
- do not rank selected checkpoints or profiles
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- scenario_sampling_failure
- lineage_invalid
- contract_violation
- metric_artifact
- behavior_regression
- training_instability
- objective_overfit

## Scoreboard

- milestone: m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation
- type: infrastructure
- checkpoint: runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json
- success_rate: 0.06685714285714285
- termination_rate: None
- clearance_margin_mean: 6.963316190636537
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_linked_measured_validation_pass_route_to_result_audit
- reason: M2413 completes 5250/5250 source-linked measured episodes reset targets 350 selected 15 family membership rows 18300 failure/validation/metadata/metric/contract/guardrail 0 outcome offtrack-dominated offtrack_rate 0.7424761904761905 no ranking/verdict claims

## Next Blocker

m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit
