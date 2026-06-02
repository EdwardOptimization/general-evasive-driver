# M2339 Paper-Route Current-Sim Support Coverage Gap Source Mapping Design

- status: completed
- result_class: `support_coverage_gap_source_mapping_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2339-paper-route-current-sim-support-coverage-gap-source-mapping-design.json`
- parent synthesis: `docs/m2338-paper-route-current-sim-residual-task-quality-branch-synthesis.md`
- admitted implementation: `artifact-only`
- target rows: `23` support-policy coverage gaps from M2336
- reset/rollout/policy action in M2339: `false`
- measured execution in M2339: `false`
- training/replay/PPO in M2339: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2338 selected the 23-row support-policy coverage gap bucket as the largest
remaining actionable current-sim task-quality blocker:

```text
support-policy coverage gaps: 23
scenario/support redesign gaps: 12
R4 post-collision blocked: 12
metric edge rows: 1
```

M2339 designs an artifact-only source mapping over those 23 rows. The goal is
not to rank support policies, select a controller, or judge driver performance.
The goal is to decide whether the coverage gaps are:

```text
source-diverse support-policy coverage gaps;
source-concentrated scenario/support redesign gaps;
role-specific metric edge cases;
or under-specified rows requiring user review before controller comparison.
```

## Inputs

The implementation should use existing artifacts only:

```text
primary residual rows:
  runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/residual_rescore_rows.csv

role and route summaries:
  runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/role_rescore_summary.csv
  runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/route_rescore_summary.csv

scenario metadata and support counts:
  runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv
  runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv
  runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv
```

Filter:

```text
rescore_route_label == support_policy_coverage_gap
```

Expected target:

```text
coverage_gap_row_count: 23
roles:
  R2_handling_limit_drift_capable_avoidance: 7
  R3_recovery_after_limit: 8
  R5_hidden_dynamics_robustness: 8
R0/R1/R4 included: false
```

## Source Mapping Axes

Each row should preserve or derive these axes:

```text
scenario_spec_id
scenario_family_id
role_family
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
best_support_success_count
best_support_policy_name_metadata_only
aeb_success_count / collision_count / offtrack_count
aes_success_count / collision_count / offtrack_count
envelope_aes_success_count / collision_count / offtrack_count
```

`best_support_policy_name_metadata_only` may be retained as diagnostic metadata
from the existing panel, but it must not be used to select a winner or rank
controllers.

## Derived Labels

The source mapping should derive non-ranking diagnostic labels:

```text
source_signature:
  role_family|hidden_dynamics_bucket|obstacle_longitudinal_timing_bucket|
  obstacle_lateral_offset_bucket

role_timing_lateral_signature:
  role_family|obstacle_longitudinal_timing_bucket|obstacle_lateral_offset_bucket

hidden_role_signature:
  role_family|hidden_dynamics_bucket

support_outcome_pattern:
  which support policies have any success, collision, or offtrack evidence

dominant_failure_bucket:
  collision_dominated_failure
  offtrack_dominated_failure
  mixed_collision_offtrack_failure
  max_step_noncompletion
  metric_edge_or_other

source_concentration_bucket:
  source_singleton
  source_cluster
  source_diverse

recommended_next_route:
  support_policy_coverage_materialization_candidate
  scenario_or_support_redesign_candidate
  metric_edge_audit_candidate
  needs_user_review
```

Recommended route rules should be conservative:

```text
support_policy_coverage_materialization_candidate:
  row is support_mixed or has partial success evidence and the residual appears
  support-policy specific rather than globally blocked.

scenario_or_support_redesign_candidate:
  all support policies fail in the same dominant mode, or rows concentrate in a
  narrow geometry/hidden-dynamics slice.

metric_edge_audit_candidate:
  row has noncollision/nonofftrack or safe-stop-like evidence that conflicts
  with role success semantics.

needs_user_review:
  fields are insufficient, route rules disagree, or the row cannot be assigned
  without new execution.
```

## Output Artifacts

M2340 should write:

```text
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/summary.json
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_source_rows.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_axis_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_support_policy_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_recommended_route_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/claim_boundary.csv
```

Required summary fields:

```text
coverage_gap_row_count
target_coverage_gap_row_count
role_count
role_counts
source_signature_count
max_source_signature_share
recommended_route_counts
support_policy_coverage_materialization_candidate_count
scenario_or_support_redesign_candidate_count
metric_edge_audit_candidate_count
needs_user_review_count
unclassified_count
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

M2340 should pass if:

```text
coverage_gap_row_count == 23
unclassified_count == 0
guardrail_violation_count == 0
all output artifacts exist
no reset/rollout/measured execution/training/replay/PPO/private holdout starts
no ranking, winner, paper, finite-window-vs-GRU, or self-ID claim is made
```

M2340 should fail closed if required join fields are missing or if source
mapping cannot separate the coverage rows from redesign candidates without new
execution.

## Decision Tree After M2340

If source mapping shows source-diverse, support-policy-specific partial support:

```text
route to bounded support-policy coverage materialization design
```

If source mapping shows concentrated failures by geometry, hidden condition, or
dominant failure mode:

```text
route to scenario/support redesign design
```

If metric-like edge rows dominate:

```text
route to metric-edge semantics audit
```

If rows are mixed and no artifact-only decision is justified:

```text
stop for user review before more local-search milestones
```

## Blocked Routes

Blocked in M2339 and M2340:

```text
direct controller-family comparison;
support-policy ranking;
controller winner selection;
driver checkpoint promotion;
training or PPO repair;
finite-window vs GRU comparison;
level3 self-ID claim;
paper-level current-sim result.
```

## Follow-Up Manifest

```text
experiments/manifests/m2340-paper-route-current-sim-support-coverage-gap-source-mapping-implementation.json
```
