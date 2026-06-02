# M2324 Paper-Route Current-Sim Scenario Task-Family Role-Stratified Residual Redesign Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_role_stratified_residual_redesign_pass`
- manifest: `experiments/manifests/m2324-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-implementation.json`
- design doc: `docs/m2323-paper-route-current-sim-scenario-task-family-role-stratified-residual-semantics-support-redesign-design.md`
- summary: `runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign.py`
- focused tests: `tests/test_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign.py`
- reset/rollout/policy action in M2324: `false`
- training/replay/PPO in M2324: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign \
  --residual-scenario-rows runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv \
  --episode-rows runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv \
  --output-dir runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign \
  --target-residual-scenario-count 48 \
  --target-r4-mitigation-row-count 12 \
  --target-coverage-row-count 23 \
  --target-redesign-row-count 12 \
  --next-blocker m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit
```

## Result

M2324 materialized the role-stratified residual redesign artifacts:

```text
input_residual_scenario_count: 48
role_stratified_residual_row_count: 48
R4 mitigation rows: 12
R2/R3/R5 coverage rows: 23
R2/R3/R5 redesign rows: 12
metric edge rows: 1
guardrail_violation_count: 0
```

Design route labels:

```text
r4_mitigation_metric_availability_gap: 12
support_policy_coverage_materialization_required: 23
scenario_or_support_redesign_materialization_required: 12
metric_semantics_edge_case: 1
```

Written artifacts:

```text
summary.json
role_stratified_residual_rows.csv
r4_mitigation_metric_availability.csv
r2_r3_r5_coverage_redesign_rows.csv
axis_route_summary.csv
claim_boundary.csv
run_state.json
```

## R4 Metric Availability

All required mitigation-severity fields are absent from the current M2318/M2321
artifacts:

```text
impact_speed_mps: missing
delta_v_at_impact_mps: missing
time_to_collision_s: missing
collision_angle_or_side: missing
post_event_speed_mps: missing
post_event_yaw_rate_abs: missing
post_event_offtrack_overshoot: missing
recoverability_window_success: missing
```

The current artifacts do contain coarse proxy columns:

```text
collision
outcome_bucket
termination_reason
min_clearance_margin
max_off_track_overshoot
time_to_first_off_track_s
high_sideslip_fraction
action_rate_mean
return
```

Those proxies are useful for diagnostics, but they are not enough to claim R4
mitigation performance.

## Claim Boundary

Allowed claims:

```text
role-stratified residual redesign artifacts were materialized;
R4 mitigation metric availability gap was identified.
```

Blocked claims:

```text
mitigation performance was measured;
R4 mitigation is solved;
support policies are ranked;
residual support is solved;
paper-level benchmark evidence is complete;
finite-window vs GRU is decided;
level3 self-identification is shown.
```

## Follow-Up

Pre-register result audit:

```text
experiments/manifests/m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit.json
```
