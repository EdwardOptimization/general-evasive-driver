# M2342 Paper-Route Current-Sim Scenario Support Redesign Consolidation Design

- status: completed
- result_class: `scenario_support_redesign_consolidation_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2342-paper-route-current-sim-scenario-support-redesign-consolidation-design.json`
- parent audit: `docs/m2341-paper-route-current-sim-support-coverage-gap-source-mapping-result-audit.md`
- admitted implementation: `artifact-only`
- target redesign-related rows: `26`
- secondary coverage-materialization rows: `9`
- reset/rollout/policy action in M2342: `false`
- measured execution in M2342: `false`
- training/replay/PPO in M2342: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2341 shows that the dominant current-sim task-quality blocker is no longer the
old 23-row coverage bucket as a whole. After source mapping:

```text
original scenario/support redesign gaps from M2336: 12
remapped redesign candidates from M2340: 14
combined redesign-related rows: 26
secondary coverage-materialization rows: 9
```

M2342 designs an artifact-only consolidation so the project can decide what
scenario/support redesign actually means before any new rollout, training,
coverage materialization, or controller comparison.

## Inputs

M2343 should read:

```text
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/residual_rescore_rows.csv
runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_source_rows.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_axis_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_recommended_route_summary.csv
```

Target sets:

```text
original_redesign_gap:
  M2336 residual_rescore_rows where
  rescore_route_label == scenario_or_support_redesign_gap

remapped_coverage_redesign_candidate:
  M2340 coverage_gap_source_rows where
  recommended_next_route == scenario_or_support_redesign_candidate

secondary_coverage_materialization:
  M2340 coverage_gap_source_rows where
  recommended_next_route == support_policy_coverage_materialization_candidate
```

Expected counts:

```text
original_redesign_gap_count: 12
remapped_coverage_redesign_candidate_count: 14
combined_redesign_related_row_count: 26
secondary_coverage_materialization_row_count: 9
```

## Consolidated Row Schema

M2343 should write one row per unique redesign-related scenario:

```text
scenario_spec_id
redesign_source
role_family
scenario_family_id
sampled_obstacle_label
same_scene_group_id
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
initial_speed_mps
track_radius_m
track_width_m
actor_contract_id
support_label
dominant_failure_mode
dominant_failure_bucket
source_signature
role_timing_lateral_signature
hidden_role_signature
aeb_success_count / collision_count / offtrack_count
aes_success_count / collision_count / offtrack_count
envelope_aes_success_count / collision_count / offtrack_count
redesign_theme
redesign_priority_bucket
recommended_redesign_route
redesign_reason
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
```

`redesign_source` should be one of:

```text
original_m2336_redesign_gap
remapped_m2340_coverage_redesign_candidate
```

The implementation should fail closed if the combined set is not 26 unique
scenario ids.

## Derived Themes

M2343 should derive conservative non-ranking themes:

```text
offtrack_geometry_pressure:
  offtrack-dominated rows, especially lateral-offset rows.

collision_timing_pressure:
  collision-dominated rows, especially late_close or centerline rows.

hidden_dynamics_stress:
  rows concentrated in low_mu, weak_brake, slow_steer_actuator, or
  tire_stiffness_shift.

role_recovery_or_drift_task_quality:
  R2/R3 rows where handling-limit or recovery semantics may need role-specific
  redesign.

hidden_dynamics_robustness_task_quality:
  R5 rows where same-scene hidden-dynamics variation appears too hard for the
  current support panel.
```

Recommended redesign route should be one of:

```text
geometry_timing_rebalance_candidate
hidden_dynamics_range_rebalance_candidate
role_semantics_or_success_metric_review_candidate
support_policy_after_redesign_candidate
needs_user_review
```

Suggested routing rules:

```text
offtrack-dominated + lateral offset:
  geometry_timing_rebalance_candidate

collision-dominated + late_close:
  geometry_timing_rebalance_candidate

weak_brake / low_mu / slow_steer_actuator / tire_stiffness_shift concentration:
  hidden_dynamics_range_rebalance_candidate unless geometry pressure dominates

role-specific rows with mixed route evidence:
  role_semantics_or_success_metric_review_candidate

rows that cannot be classified artifact-only:
  needs_user_review
```

## Output Artifacts

M2343 should write:

```text
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/summary.json
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/consolidated_redesign_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/secondary_coverage_materialization_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_axis_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_route_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_source_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/claim_boundary.csv
```

Required summary fields:

```text
original_redesign_gap_count
remapped_coverage_redesign_candidate_count
combined_redesign_related_row_count
unique_redesign_scenario_count
secondary_coverage_materialization_row_count
redesign_theme_counts
recommended_redesign_route_counts
needs_user_review_count
duplicate_redesign_scenario_count
guardrail_violation_count
environment_reset_started
environment_rollout_started
measured_rollout_started
training_started
replay_started
ppo_used
support_policy_ranking_claim_made
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
```

## Acceptance Criteria

M2343 should pass if:

```text
original_redesign_gap_count == 12
remapped_coverage_redesign_candidate_count == 14
combined_redesign_related_row_count == 26
unique_redesign_scenario_count == 26
secondary_coverage_materialization_row_count == 9
needs_user_review_count == 0
duplicate_redesign_scenario_count == 0
guardrail_violation_count == 0
all required artifacts exist
```

M2343 should fail closed if:

```text
required join fields are missing;
redesign rows cannot be deduplicated;
classification produces unreviewed rows;
any reset/rollout/training/ranking path starts;
or the output claims residual support solved.
```

## Decision Tree After M2343

If the 26 rows are dominated by geometry/timing pressure:

```text
route to bounded scenario geometry/timing rebalance design
```

If hidden-dynamics stress dominates:

```text
route to hidden-dynamics range rebalance design
```

If role semantics dominate:

```text
route to role-specific success semantics review
```

If redesign rows remain mixed but classified:

```text
route to branch synthesis before choosing between redesign and support coverage
```

If any rows are unclassified:

```text
stop for user review
```

## Blocked Routes

Blocked in M2342 and M2343:

```text
direct scenario redesign execution;
support-policy coverage materialization;
controller-family comparison;
support-policy ranking;
driver checkpoint promotion;
training or PPO repair;
finite-window vs GRU comparison;
level3 self-ID claim;
paper-level current-sim result.
```

## Follow-Up Manifest

```text
experiments/manifests/m2343-paper-route-current-sim-scenario-support-redesign-consolidation-implementation.json
```
