# m2399-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-implementation Research Review

## Summary

- Generated at UTC: 20260602T121229Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: effective_candidate_measured_outcome_localization_pass_route_to_result_audit
- Decision reason: M2399 materializes 1313 localization slices from M2397 rows: offtrack 1132 collision 364 R4 57 high-priority offtrack 658 guardrail 0 no rerun/ranking/verdict claims

## Hypothesis

M2397 measured outcomes can be localized into actionable offtrack, collision-guardrail, R4 mitigation, and diagnostic-only slices without rerun, repair execution, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_effective_candidate_measured_outcome_localization
- parent_dataset: docs/m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit.md, docs/m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation.md, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/episode_rows.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_candidate.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_candidate_profile.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_repair_family.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_role_family.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/aggregate_by_hidden_dynamics_bucket.csv, runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/claim_boundary.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit.json
- parent_objective: materialize artifact-only localization slices from the complete M2397 measured panel
- derived_from: m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit, m2397-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-implementation
- blocked_by: M2398 accepts M2397 as complete but offtrack-dominated, offtrack/collision/R4 semantics are not yet localized into actionable slice rows, repair or scenario decisions are inadmissible before localization
- supersedes: manual interpretation of M2397 aggregate tables, direct repair from global offtrack rate, candidate/profile ranking from diagnostic aggregates
- invalidates: None

## Success Criteria

- runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/summary.json exists
- source_episode_count equals 30735
- slice rows preserve M2397 lineage fields
- offtrack target, collision guardrail, R4 mitigation semantics, and diagnostic-only classes are separated
- ranking_admissible_count equals 0 and winner_selected_count equals 0
- paper finite-window-vs-GRU level3 self-ID scenario-redesign training-repair and current-sim verdict claims remain false

## Failure Criteria

- M2399 reruns rollout or executes repair/training/replay/PPO
- M2399 ranks candidates, ranks profiles, or selects a winner
- M2399 drops candidate/pack/scenario/checkpoint lineage
- M2399 cannot reconcile localization counts with M2397 summary
- M2399 makes paper finite-window-vs-GRU current-sim verdict or level3 self-ID claims

## Evidence Gates

- M2399 must read only M2397 artifact rows and must not rerun rollout
- M2399 must materialize slice rows for offtrack targets, collision guardrails, R4 mitigation semantics, and diagnostic-only categories
- M2399 must preserve candidate/profile/pack/role/hidden/timing/lateral lineage without ranking or winner selection
- M2399 must keep paper, finite-window-vs-GRU, level3 self-ID, scenario-redesign, training-repair, and current-sim verdict claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun M2397
- do not run new rollout
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not inject hidden or oracle features
- do not tune controller profiles
- do not rank support policies or controller families
- do not rank effective candidates
- do not select a winner
- do not overwrite the active scenario config
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

- milestone: m2399-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-implementation
- type: infrastructure
- checkpoint: runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: effective_candidate_measured_outcome_localization_pass_route_to_result_audit
- reason: M2399 materializes 1313 localization slices from M2397 rows: offtrack 1132 collision 364 R4 57 high-priority offtrack 658 guardrail 0 no rerun/ranking/verdict claims

## Next Blocker

m2400-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-result-audit
