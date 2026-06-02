# M2401 Paper-Route Current-Sim Dual-Axis Effective Candidate Actionable Target Consolidation Implementation

- status: completed
- result class: `current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass`
- manifest: `experiments/manifests/m2401-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation.py`
- focused tests: `3 passed`
- summary: `runs/m2401_paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation/summary.json`
- source localization: `runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/slice_rows.csv`
- rerun/new rollout in M2401: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2401 consolidates M2399 raw localization slices into compact target and
guardrail tables.

Summary:

```text
result_class: current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass
source_slice_row_count: 1313
target_slice_row_count: 1313
consolidated_row_count: 1313
offtrack_repair_target_row_count: 203
collision_guardrail_row_count: 65
r4_mitigation_semantics_row_count: 57
diagnostic_guardrail_row_count: 1034
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Consolidated route counts:

```text
collision_guardrail: 5
diagnostic_guardrail: 1034
diagnostic_only: 14
offtrack_repair_target: 143
offtrack_repair_target_with_collision_guardrail: 60
r4_mitigation_semantics: 57
```

Actionability class counts:

```text
diagnostic_guardrail: 1034
geometry_timing: 6
hidden_dynamics: 7
r4_mitigation_semantics: 57
repair_family_conditioned_hidden_dynamics: 21
repair_family_conditioned_role: 15
repair_family_surface: 3
role_conditioned_geometry_timing: 30
role_conditioned_hidden_dynamics: 19
role_semantics: 13
source_slice_surface: 108
```

## Top Consolidated Targets

Top offtrack repair targets:

```text
obstacle_lateral_offset_bucket=centerline episodes=16710 offtrack=0.8709156193895871 collision=0.06918013165769 class=geometry_timing
obstacle_longitudinal_timing_bucket=early_far episodes=11760 offtrack=0.9122448979591836 collision=0.02534013605442177 class=geometry_timing
repair_family=priority_offtrack_containment_repair episodes=11115 offtrack=0.9159694107062528 collision=0.030589293747188485 class=repair_family_surface
obstacle_longitudinal_timing_bucket=mid episodes=9990 offtrack=0.8435435435435436 collision=0.1021021021021021 class=geometry_timing
hidden_dynamics_bucket=slow_steer_actuator episodes=8835 offtrack=0.8452744765138653 collision=0.09734012450481042 class=hidden_dynamics
repair_family=offtrack_containment_repair episodes=8340 offtrack=0.8267386091127098 collision=0.0908872901678657 class=repair_family_surface
```

Top collision guardrails:

```text
role_family+obstacle_lateral_offset_bucket=R5_hidden_dynamics_robustness|right_offset episodes=1260 offtrack=0.5365079365079365 collision=0.4388888888888889 class=role_conditioned_geometry_timing
role_family+obstacle_longitudinal_timing_bucket=R5_hidden_dynamics_robustness|late_close episodes=1260 offtrack=0.5365079365079365 collision=0.4388888888888889 class=role_conditioned_geometry_timing
role_family+obstacle_lateral_offset_bucket=R2_handling_limit_drift_capable_avoidance|right_offset episodes=1110 offtrack=0.6594594594594595 collision=0.3216216216216216 class=role_conditioned_geometry_timing
repair_family+hidden_dynamics_bucket=guarded_offtrack_containment_repair|weak_brake episodes=405 offtrack=0.4962962962962963 collision=0.3728395061728395 class=repair_family_conditioned_hidden_dynamics
repair_family+hidden_dynamics_bucket=guarded_offtrack_containment_repair|same_scene_balanced_panel episodes=90 offtrack=0.6777777777777778 collision=0.3111111111111111 class=repair_family_conditioned_hidden_dynamics
```

Top R4 mitigation semantics:

```text
role_family=R4_unavoidable_mitigation episodes=975 offtrack=0.3958974358974359 collision=0.598974358974359
sampled_obstacle_label=unavoidable episodes=975 offtrack=0.3958974358974359 collision=0.598974358974359
scenario_family_id=R4 episodes=975 offtrack=0.3958974358974359 collision=0.598974358974359
repair_family+role_family=guarded_offtrack_containment_repair|R4_unavoidable_mitigation episodes=675 offtrack=0.23851851851851852 collision=0.76
role_family+obstacle_lateral_offset_bucket=R4_unavoidable_mitigation|centerline episodes=600 offtrack=0.36666666666666664 collision=0.625
```

Candidate/profile/pack/global rows were consolidated as diagnostic guardrails,
not repair targets. This preserves the no-ranking boundary.

## Claim Boundary

Supported:

```text
M2401 materialized compact target-consolidation artifacts from M2399 slices and
kept candidate/profile/pack axes diagnostic-only.
```

Blocked:

```text
effective-candidate ranking
controller-family ranking
winner selection
repair execution
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Route Decision

Decision:

```text
effective_candidate_actionable_target_consolidation_pass_route_to_result_audit
```

Next milestone:

```text
m2402-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-result-audit
```

M2402 should audit whether M2401 target categories are ready for bounded repair
planning, branch synthesis, or stop. It must not rerun rollout, execute repair,
train, rank candidates/profiles, select a winner, or make paper/self-ID/current-
sim verdict claims.
