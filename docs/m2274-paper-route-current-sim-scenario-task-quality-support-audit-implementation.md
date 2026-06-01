# M2274 Paper-Route Current-Sim Scenario/Task-Quality Support Audit Implementation

- status: completed
- result: `current_sim_scenario_task_quality_support_audit_pass`
- manifest: `experiments/manifests/m2274-paper-route-current-sim-scenario-task-quality-support-audit-implementation.json`
- run: `runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/summary.json`

## Scope

M2274 implemented and ran the no-rerun artifact support audit admitted by
M2273. It read only existing episode rows and training matrices:

```text
episode rows:
  M2244 baseline selected-checkpoint localization
  M2253 generic reward repair localization
  M2265 targeted containment localization

training matrices:
  M2227 short-v0 matched-budget configs
  M2233 medium-v1 matched-budget configs
  M2248 generic reward extension configs
  M2259 targeted containment configs
```

No reset, rollout, policy action, measured execution, training, replay, PPO,
private holdout, promotion, ranking, winner selection, paper-level result,
finite-window-vs-GRU conclusion, or level3 self-identification claim was made.

## Result

The audit completed cleanly:

```text
result_class: current_sim_scenario_task_quality_support_audit_pass
episode_row_count: 1440
training_matrix_row_count: 60
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
primary_route: scenario_task_family_generation_design
```

Contract support in the four training matrices is clean:

```text
hidden_oracle_actor_input_rows: 0
wheel_or_slip_actor_input_rows: 0
reference_or_ttc_actor_input_rows: 0
training_started_rows: 0
policy_action_executed_rows: 0
ranking_admissible_rows: 0
winner_selected_rows: 0
```

## Role Support

Explicit role labels exist for only three of the six M2273 role families:

```text
R0_stable_avoidable: present_label, 180 rows
R1_aeb_infeasible_stable_aes: missing, 0 rows
R2_handling_limit_drift_capable_avoidance: present_label, 840 rows
R3_recovery_after_limit: proxy_present_not_role_label, 701 rows
R4_unavoidable_mitigation: present_label, 420 rows
R5_hidden_dynamics_robustness: proxy_present_not_role_label, 1440 rows
```

Interpretation:

- `aes_feasible`, `drift_required`, and `unavoidable` are useful but too coarse.
- Recovery and hidden-dynamics robustness have diagnostic columns, but they are
  not explicit scenario roles.
- AEB-infeasible stable AES is absent as an explicit task family.

## Scenario-Axis Support

Supported direct axes:

```text
initial_speed_bucket
road_width_bucket
road_curvature_bucket
friction_bucket
brake_scale_bucket
actuator_lag_bucket
vehicle_mass_or_inertia_bucket
role_family
```

Missing or incomplete axes:

```text
obstacle_longitudinal_timing_bucket: missing
obstacle_lateral_offset_bucket: missing
recovery_window_bucket: partial
```

The missing obstacle timing and lateral offset metadata are high-severity gaps
for benchmark-pack generation because they control whether scenarios can be
balanced by actual obstacle geometry instead of only by outcomes.

## Metric Coverage

Primary metrics are computable from existing rows:

```text
success_rate
collision_rate
offtrack_rate
spin_or_high_sideslip_rate
clearance_margin_tail
impact_speed_or_mitigation_proxy
recovery_success_rate
post_maneuver_stability_rate
control_smoothness
role_completion_rate
```

Metric coverage is therefore not the immediate blocker. The blocker is role and
scenario-axis support.

## Readiness Floors

Only one of five readiness floors passes:

```text
role_family_label_completeness: 3/6, fail
role_family_min_public_rows_64: 3/6, fail
role_family_present_or_proxy_support: 5/6, fail
scenario_axis_direct_support: 8/11, fail
primary_metric_coverage: 10/10, pass
```

## Route Decision

Route to:

```text
scenario_task_family_generation_design
```

M2275 should audit this result before implementation. If accepted, the next
real branch should design explicit current-sim scenario families and metadata
instrumentation for:

```text
R1_aeb_infeasible_stable_aes
R3_recovery_after_limit
R5_hidden_dynamics_robustness
obstacle longitudinal timing
obstacle lateral offset
recovery window support
```

## Artifacts

```text
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/summary.json
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/role_support.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/scenario_axis_support.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/metric_coverage.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/readiness_floor_gap.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/support_gap_report.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/training_matrix_contract_support.csv
runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/redesign_routes.csv
```

## Next

Pre-register:

```text
m2275-paper-route-current-sim-scenario-task-quality-support-audit-result-audit
```
