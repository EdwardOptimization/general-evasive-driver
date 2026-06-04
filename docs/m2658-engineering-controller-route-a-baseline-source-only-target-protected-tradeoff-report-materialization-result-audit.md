# M2658 Engineering Controller Route A Source-Only Target/Protected Tradeoff Report Materialization Result Audit

- status: completed
- decision: `accept_m2657_route_to_route_a_baseline_evidence_index_refresh`
- manifest: `experiments/manifests/m2658-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-result-audit.json`
- parent summary: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/summary.json`
- parent scenario-role report: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/scenario_role_metric_report.csv`
- parent target/protected tradeoff rows: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/target_protected_tradeoff_rows.csv`
- parent protected focus rows: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/protected_regression_focus_rows.csv`
- parent report gates: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/report_gate_evaluation.csv`
- follow-up manifest: `experiments/manifests/m2659-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-preflight.json`
- next: `m2659-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-preflight`

## Audit Result

M2658 accepts M2657 as a Route A source-only target/protected tradeoff report
materialization. The report is admitted as baseline-index input only. It is
not admitted as repair success, checkpoint promotion, validation, ranking,
success-rate, driver-performance, paper, current-sim, high-fidelity validation,
finite-window-vs-GRU, full ideal driver, or self-ID evidence.

Accepted M2657 summary:

```text
status_pass: true
source_artifacts_reanalyzed_only: true
new_repair_training_or_rollout_run: false
scenario_role_metric_report_row_count: 4
target_protected_tradeoff_row_count: 9
protected_regression_focus_row_count: 8
report_gate_evaluation_row_count: 8
target_roles: stable_avoidable, stable_aes, drift_required_recovery
protected_roles: unavoidable_mitigation
m2655_target_preservation_gates_all_passed: true
m2655_protected_component_gates_all_passed: false
m2655_target_and_protected_gates_all_passed: false
actor_contract_shape_72_action_3: true
hidden_or_oracle_actor_input_detected: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
```

Required artifacts are present:

```text
summary.json
scenario_role_metric_report.csv
target_protected_tradeoff_rows.csv
protected_regression_focus_rows.csv
report_gate_evaluation.csv
milestone doc
```

## Target/Protected Split

M2657 keeps three target roles separate from the protected mitigation role:

```text
stable_avoidable:
  role_class: target
  metric: minimum_road_margin_m
  M2648 improved/regressed: 8/0
  M2655 improved/regressed: 8/0
  M2655 gate_pass: true

stable_aes:
  role_class: target
  metric: minimum_road_margin_m
  M2648 improved/regressed: 8/0
  M2655 improved/regressed: 8/0
  M2655 gate_pass: true

drift_required_recovery:
  role_class: target
  metric: drift_tradeoff_proxy
  M2648 improved/regressed: 8/0
  M2655 improved/regressed: 8/0
  M2655 gate_pass: true

unavoidable_mitigation:
  role_class: protected
  metric: severity_proxy
  M2648 improved/regressed: 7/1
  M2655 improved/regressed: 7/1
  M2655 gate_pass: false
  excluded_from_target_success_denominator: true
```

This is the correct boundary. The target rows can be indexed as target
improvement evidence, while the protected rows remain blocking evidence. They
must not be collapsed into an ordinary success denominator.

## Protected Failure Audit

M2657 preserves the M2655 negative result:

```text
selected diagnostic candidate: m2655_softened_gap_bias
selected candidate treated as winner: false
target preservation gates all passed: true
protected component gates all passed: false
target and protected gates all passed: false
failed protected gates:
  severity_proxy_non_regression
  obstacle_penetration_non_regression
  minimum_obstacle_clearance_preservation
```

M2657 also carries forward the M2650 localized protected regression:

```text
scenario_role: unavoidable_mitigation
seed: 267101
dynamics_axis_id: fresh_fault_delay_noise
likely driver: obstacle_penetration_proxy_worsened
M2648 severity delta: +0.034052
M2655 severity delta: +0.025451
M2648 obstacle penetration delta: +0.040287
M2655 obstacle penetration delta: +0.027610
```

The M2655 mitigation-preserving repair softened the M2648 regression magnitude
on the localized row, but it did not clear the protected gates. M2658 therefore
keeps protected mitigation failure blocking for any repair success, promotion,
validation, or driver-performance interpretation.

## Actor Boundary

M2658 accepts the M2657 actor/action boundary:

```text
observation_shape: 72
action_shape: 3
actor_input_leak_flags: none
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
localization_labels_actor_visible: false
objective_gate_labels_actor_visible: false
route_decision_labels_actor_visible: false
ranking_or_winner_field_emitted: false
```

Labels, gate outcomes, route decisions, and localization fields remain artifact
metadata only. They must not be used as actor inputs in later driver training or
repair work.

## Supported Claims

M2658 supports these bounded claims:

```text
M2657 materialized a traceable Route A source-only target/protected tradeoff report.
M2657 reanalyzed existing source artifacts only and did not run repair training or rollout.
M2657 preserves the target/protected split required after the M2656 pivot.
M2657 preserves the M2655 target-pass protected-fail negative result.
M2657 is suitable as input to a Route A baseline evidence index refresh.
```

## Rejected Claims

M2658 rejects these interpretations:

```text
M2657 proves repair success.
M2657 may promote m2655_softened_gap_bias or any checkpoint.
M2657 selects a winner or ranks controller families.
M2657 computes a success-rate verdict.
M2657 is a validation result.
M2657 is driver-performance or paper-level evidence.
M2657 is finite-window-vs-GRU or self-ID evidence.
M2657 is a current-sim or high-fidelity validation verdict.
M2657 target-gate pass overrides protected mitigation regression.
```

No reset, step, rollout, replay, validation, training, PPO, source build,
adapter probe, external high-fidelity simulation, ranking, winner selection,
promotion, or success-rate computation was executed in M2658.

## Decision

Route to M2659 Route A baseline evidence index refresh after target/protected
report materialization.

M2659 should materialize a refreshed baseline evidence index that includes the
M2639 baseline evidence map, M2641 source-only panel, M2644 taxonomy, M2648 and
M2655 repair-branch evidence, M2656 pivot, and M2657 target/protected tradeoff
report. It should preserve the same claim boundary: target improvements are
indexed as engineering evidence, protected mitigation failure remains blocking,
and no ranking, promotion, validation, success-rate, driver-performance, paper,
finite-window-vs-GRU, current-sim, high-fidelity, full ideal driver, or self-ID
claim is allowed.
