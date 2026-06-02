# m2415-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-implementation Research Review

## Summary

- Generated at UTC: 20260602T150136Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_linked_measured_outcome_localization_pass_route_to_result_audit
- Decision reason: M2415 materializes artifact-only localization source episodes 5250 family rows 18300 slices 2844 offtrack 272 collision 114 R4 49 maxstep 325 speedlow 124 diagnostic 2504 no rerun/ranking/verdict claims

## Hypothesis

Artifact-only localization of M2413 rows will produce bounded diagnostic slices for offtrack/collision/R4 outcome blockers without rerun, repair, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_localization
- parent_dataset: docs/m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit.md, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_family_membership_rows.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_profile.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_family_membership.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/aggregate_by_role_family.csv
- parent_config: experiments/manifests/m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit.json
- parent_objective: materialize artifact-only localization slices from M2413 measured outcome rows
- derived_from: m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit, m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation
- blocked_by: M2413 measured outcome is offtrack-dominated, family membership is overlapping and must remain diagnostic, direct repair execution is not admissible before localization
- supersedes: direct repair from M2413 global outcome, family/profile ranking from diagnostic slices, current-sim verdict from measured-validation pass
- invalidates: None

## Success Criteria

- runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json exists
- source_episode_count is 5250
- source_family_membership_row_count is 18300
- slice_row_count is greater than 0
- offtrack localization rows are written
- collision guardrail rows are written
- R4 mitigation rows are written
- diagnostic rows are written
- rerun/repair/training/ranking/verdict claim counts remain zero

## Failure Criteria

- M2415 reruns measured validation
- M2415 executes repair or training
- M2415 ranks candidate families, profiles, or selected checkpoints
- M2415 selects a winner
- M2415 ignores family membership overlap
- M2415 makes measured driver success, current-sim, paper, FW-vs-GRU, or self-ID claims

## Evidence Gates

- M2415 must read only M2413 artifacts and not rerun measured validation
- M2415 must write localization rows and summary under its run dir
- M2415 must keep family, profile, and controller axes diagnostic-only
- M2415 must classify offtrack, collision, max-step, speed-too-low, and R4 mitigation slices
- M2415 must not execute repair, train, replay, PPO, rank, select winner, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun M2413
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
- objective_overfit

## Scoreboard

- milestone: m2415-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-implementation
- type: infrastructure
- checkpoint: runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_linked_measured_outcome_localization_pass_route_to_result_audit
- reason: M2415 materializes artifact-only localization source episodes 5250 family rows 18300 slices 2844 offtrack 272 collision 114 R4 49 maxstep 325 speedlow 124 diagnostic 2504 no rerun/ranking/verdict claims

## Next Blocker

m2416-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-result-audit
