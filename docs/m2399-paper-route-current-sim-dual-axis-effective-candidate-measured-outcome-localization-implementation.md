# M2399 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Outcome Localization Implementation

- status: completed
- result class: `current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass`
- manifest: `experiments/manifests/m2399-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization.py`
- focused tests: `3 passed`
- summary: `runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/summary.json`
- source measured panel: `runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/episode_rows.csv`
- rerun/new rollout in M2399: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2399 materializes artifact-only localization slices from the complete M2397
measured panel.

Summary:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass
source_episode_count: 30735
target_episode_count: 30735
source_candidate_count: 54
source_profile_count: 5
source_role_family_count: 6
slice_row_count: 1313
offtrack_target_slice_count: 1132
collision_guardrail_slice_count: 364
r4_mitigation_semantics_slice_count: 57
diagnostic_only_slice_count: 96
high_priority_offtrack_slice_count: 658
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Route-class counts:

```text
collision_guardrail: 28
diagnostic_only: 96
offtrack_target: 796
offtrack_target_with_collision_guardrail: 336
r4_mitigation_semantics: 57
```

Slice-axis counts:

```text
candidate_id: 54
candidate_id+pack_id: 262
candidate_id+profile_name: 270
candidate_id+role_family: 81
candidate_id+role_family+hidden_dynamics_bucket: 207
global: 1
hidden_dynamics_bucket: 8
obstacle_lateral_offset_bucket: 3
obstacle_longitudinal_timing_bucket: 3
pack_id: 5
pack_id+profile_name+role_family: 150
profile_name: 5
profile_name+role_family: 30
repair_family: 3
repair_family+hidden_dynamics_bucket: 23
repair_family+role_family: 17
role_family: 6
role_family+hidden_dynamics_bucket: 22
role_family+obstacle_lateral_offset_bucket: 18
role_family+obstacle_longitudinal_timing_bucket: 18
sampled_obstacle_label: 4
scenario_family_id: 6
source_slice_axis: 9
source_slice_axis+source_slice_value: 54
source_slice_value: 54
```

## Top Localized Slices

Top offtrack target slices:

```text
global=all episodes=30735 success=0.04054010086220921 collision=0.10157800553115341 offtrack=0.8425898812428827 route=offtrack_target
obstacle_lateral_offset_bucket=centerline episodes=16710 success=0.042788749251944945 collision=0.06918013165769 offtrack=0.8709156193895871 route=offtrack_target
sampled_obstacle_label=drift_required episodes=14955 success=0.0 collision=0.16817118020728852 offtrack=0.8146439317953862 route=offtrack_target_with_collision_guardrail
obstacle_longitudinal_timing_bucket=early_far episodes=11760 success=0.04030612244897959 collision=0.02534013605442177 offtrack=0.9122448979591836 route=offtrack_target
repair_family=guarded_offtrack_containment_repair episodes=11280 success=0.02331560283687943 collision=0.1794326241134752 offtrack=0.7820035460992908 route=offtrack_target_with_collision_guardrail
```

Top collision guardrail slices:

```text
sampled_obstacle_label=drift_required episodes=14955 success=0.0 collision=0.16817118020728852 offtrack=0.8146439317953862 route=offtrack_target_with_collision_guardrail
repair_family=guarded_offtrack_containment_repair episodes=11280 success=0.02331560283687943 collision=0.1794326241134752 offtrack=0.7820035460992908 route=offtrack_target_with_collision_guardrail
obstacle_longitudinal_timing_bucket=late_close episodes=8985 success=0.0439621591541458 collision=0.20077907623817473 offtrack=0.750361713967724 route=offtrack_target_with_collision_guardrail
obstacle_lateral_offset_bucket=right_offset episodes=6120 success=0.03643790849673203 collision=0.19558823529411765 offtrack=0.75359477124183 route=offtrack_target_with_collision_guardrail
repair_family+role_family=guarded_offtrack_containment_repair|R2_handling_limit_drift_capable_avoidance episodes=4710 success=0.0 collision=0.162208067940552 offtrack=0.8199575371549894 route=offtrack_target_with_collision_guardrail
```

Top R4 mitigation semantics slices:

```text
role_family=R4_unavoidable_mitigation episodes=975 success=0.0 collision=0.598974358974359 offtrack=0.3958974358974359 route=r4_mitigation_semantics
scenario_family_id=R4 episodes=975 success=0.0 collision=0.598974358974359 offtrack=0.3958974358974359 route=r4_mitigation_semantics
sampled_obstacle_label=unavoidable episodes=975 success=0.0 collision=0.598974358974359 offtrack=0.3958974358974359 route=r4_mitigation_semantics
repair_family+role_family=guarded_offtrack_containment_repair|R4_unavoidable_mitigation episodes=675 success=0.0 collision=0.76 offtrack=0.23851851851851852 route=r4_mitigation_semantics
role_family+obstacle_lateral_offset_bucket=R4_unavoidable_mitigation|centerline episodes=600 success=0.0 collision=0.625 offtrack=0.36666666666666664 route=r4_mitigation_semantics
```

These rows are diagnostic targets. They are not ranked winners and do not prove
which controller family or candidate is best.

## Claim Boundary

Supported:

```text
M2399 generated artifact-only localization slices from M2397 rows and separated
offtrack targets, collision guardrails, R4 mitigation semantics, and
diagnostic-only slices while preserving the no-ranking claim boundary.
```

Blocked:

```text
effective-candidate ranking
controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```

## Route Decision

Decision:

```text
effective_candidate_measured_outcome_localization_pass_route_to_result_audit
```

Next milestone:

```text
m2400-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-result-audit
```

M2400 should audit whether M2399 localization is actionable enough to route to
target consolidation, guardrail repair planning, branch synthesis, or stop. It
must not rerun rollout, execute repair, train, rank candidates/profiles, select
a winner, or make paper/self-ID/current-sim verdict claims.
