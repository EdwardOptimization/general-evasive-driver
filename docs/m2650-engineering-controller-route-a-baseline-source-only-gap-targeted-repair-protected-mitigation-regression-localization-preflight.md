# M2650 Engineering Controller Route A Protected Mitigation Regression Localization Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization_preflight_pass`
- manifest: `experiments/manifests/m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-protected-mitigation-regression-localization-preflight.json`
- summary: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/summary.json`
- mitigation regression rows: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/mitigation_regression_rows.csv`
- metric component delta rows: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/metric_component_delta_rows.csv`
- localization findings: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/localization_findings.json`
- follow-up manifest: `experiments/manifests/m2651-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-synthesis.json`
- next: `m2651-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-synthesis`

## Result

M2650 reanalyzed existing M2641 baseline behavior rows, M2648
post-repair behavior rows, M2648 repair-gate rows, and the M2649
audit document. It did not run repair, training, reset, rollout,
replay, validation, ranking, promotion, or success-rate computation.

```text
matched_protected_mitigation_pair_count: 8
mitigation_regression_row_count: 1
metric_component_delta_row_count: 120
protected_gate_improved_row_count: 7
protected_gate_regressed_row_count: 1
metric_artifact_detected: False
```

## Localized Regression

The single regressed protected mitigation row is:

```text
subject: m2537_mitigation_preserving_policy
scenario_role: unavoidable_mitigation
seed: 267101
dynamics_axis_id: fresh_fault_delay_noise
severity_proxy: 3.9538638168212126 -> 3.9879161809815282
severity_delta: 0.03405236416031565
minimum_obstacle_clearance_m: -1.4368722011875867 -> -1.4771592870702182
obstacle_penetration_proxy_m: 1.4368722011875867 -> 1.4771592870702182
collision_speed_proxy: 3.3590230443570963 -> 3.322625253932567
impact_angle_proxy: 0.4529587380097288 -> 0.44348818149320834
minimum_road_margin_m: 0.8996198544251907 -> 0.9491281478101072
```

Likely severity-proxy component driver:

```text
obstacle_penetration_proxy_worsened
severity increased while collision speed did not; row-level obstacle penetration proxy deepened
```

Regressed component metrics on the failing row:

```text
severity_proxy, minimum_obstacle_clearance_m, mitigation_delta_against_reference
```

Improved component metrics on the same row:

```text
collision_speed_proxy, impact_angle_proxy, minimum_road_margin_m, final_road_margin_m, maximum_abs_lateral_velocity, maximum_abs_yaw_rate, maximum_abs_lateral_position, final_abs_lateral_velocity, final_abs_yaw_rate, command_delta_l1_mean, simultaneous_throttle_brake_fraction
```

## Interpretation Boundary

This is a protected-reference localization. It supports routing to
mitigation-preserving repair synthesis because the regression is real
at the row-level proxy evidence and not currently explained as a gate
calculation artifact. It does not support driver-performance,
promotion, ranking, success-rate, validation, paper, finite-window-vs-GRU,
current-sim, high-fidelity, or self-ID claims.

## Decision

Route to M2651 mitigation-preserving repair synthesis before any second
repair execution. The synthesis must preserve the protected mitigation
reference and should decide whether to repair the objective, repair the
artifact semantics, run a bounded implementation repair, or stop.
