# M1771 Paper-Route Metric-Specific Bounded Panel Materialization Preflight

- status: completed
- result class: `metric_specific_bounded_panel_materialization_preflight_pass`
- summary: `runs/m1771_metric_specific_bounded_panel_materialization_preflight/summary.json`
- parent design: `docs/m1770-paper-route-metric-specific-bounded-panel-design.md`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1771 materializes the M1770 bounded metric-specific panel without environment
reset, policy rollout, training, replay, PPO, profile tuning, ranking, or
paper-level claims.

The preflight passes:

```text
panel_spec_count: 24 / 24
role_panel_count: 4 / 4
specs_per_role: 6 each
profile_count: 12 / 12
panel_cell_count: 288 / 288
role_balance_passed: true
missing_config_count: 0
missing_checkpoint_count: 0
contract_violation_count: 0
labels_enter_actor_input_count: 0
unsupported_faults_treated_as_covered_count: 0
guardrail_violation_count: 0
```

## Role Panels

```text
stable_avoidance_aes:
  specs: 6
  cells: 72
  families: ordinary_stable_avoidance, aeb_infeasible_stable_aes
  metric family: avoidance_success

drift_required_recovery:
  specs: 6
  cells: 72
  families: drift_required_avoidance
  metric family: controlled_drift_recovery

hidden_dynamics_robustness:
  specs: 6
  cells: 72
  families: hidden_dynamics_stress
  metric family: hidden_dynamics_robustness

unavoidable_mitigation:
  specs: 6
  cells: 72
  families: unavoidable_mitigation
  metric family: collision_mitigation
```

The selected source specs are recorded in
`bounded_panel_role_summary.csv`. M1771 creates new bounded panel spec IDs while
preserving each original `m1728_scenario_spec_id`.

## Metric Contract

M1771 writes a role-specific metric contract:

```text
stable_avoidance_aes:
  benchmark_success
  avoidance_success
  off_track_violation
  off_track_severity_proxy
  recovery_success
  recovery_time_proxy

drift_required_recovery:
  benchmark_success
  avoidance_success
  controlled_drift_recovery_success
  drift_used
  recovery_success
  recovery_time_proxy

hidden_dynamics_robustness:
  hidden_dynamics_robustness
  avoidance_success
  collision_mitigation_score
  off_track_violation
  impact_severity_proxy

unavoidable_mitigation:
  collision_mitigation_score
  impact_severity_proxy
  impact_speed_proxy
  impact_beta_abs
  impact_yaw_rate_abs
  off_track_severity_proxy
```

The contract is diagnostic-only and does not rank profiles. It marks mitigation
rows as severity/mitigation rows rather than ordinary obstacle-pass rows.

## Artifacts

```text
runs/m1771_metric_specific_bounded_panel_materialization_preflight/summary.json
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_role_summary.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_metric_contract.json
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_metric_contract.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/unsupported_feature_boundary.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/contract_violations.csv
```

`bounded_panel_matrix.csv` contains `288` cells:

```text
24 selected specs x 12 existing controller profiles
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- unsupported faults treated as covered: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-rollout materialization of a 24-spec, 288-cell role-separated public
  diagnostic panel;
- metric-contract materialization;
- profile/config/checkpoint presence for all 288 cells;
- human-view actor contract check passed for selected env configs.

Unsupported:

- reset feasibility;
- policy rollout success;
- controller-family ranking;
- profile promotion;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Decision

Route to M1772 materialization result audit before reset feasibility or measured
execution.

M1772 should audit whether this materialization is coherent enough to admit a
reset-only feasibility preflight, execution design, or a metric-contract repair.
