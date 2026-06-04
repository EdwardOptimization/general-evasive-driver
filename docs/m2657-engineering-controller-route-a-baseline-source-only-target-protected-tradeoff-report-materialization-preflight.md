# M2657 Route A Source-Only Target/Protected Tradeoff Report

- status: completed
- result_class: `engineering_controller_route_a_source_only_target_protected_tradeoff_report_materialization_preflight_pass`
- manifest: `experiments/manifests/m2657-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-preflight.json`
- summary: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/summary.json`
- scenario-role report: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/scenario_role_metric_report.csv`
- target/protected tradeoff rows: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/target_protected_tradeoff_rows.csv`
- protected regression focus rows: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/protected_regression_focus_rows.csv`
- report gates: `runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/report_gate_evaluation.csv`
- source rows: baseline 32, M2648 32, M2655 32 for `m2537_mitigation_preserving_policy`
- scenario roles: 3 target and 1 protected
- target gate rows passed: 4
- protected gate rows failed: 4
- M2655 selected diagnostic candidate: `m2655_softened_gap_bias`; not a winner and not promoted
- M2655 target preservation gates all passed: True
- M2655 protected component gates all passed: False
- M2655 target and protected gates all passed: False
- failed protected gates: `severity_proxy_non_regression;obstacle_penetration_non_regression;minimum_obstacle_clearance_preservation`
- M2650 localized protected regression: True (obstacle_penetration_proxy_worsened)
- M2655 protected focus rows with component regression: 2 / 8
- report gates pass: True
- actor/action boundary: P0 observation 72 action 3; no hidden/oracle actor input
- supported operational claim: Route A source-only scenario-role target/protected tradeoff report was materialized from existing evidence
- rejected claims: repair success, driver performance, controller ranking, winner selection, checkpoint promotion, success-rate verdict, validation result, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation result, full ideal driver completion, or self-ID evidence
- follow-up manifest: `experiments/manifests/m2658-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-result-audit.json`
- next: `m2658-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-result-audit`

## Scenario-Role Split

- `stable_avoidable` target metric `minimum_road_margin_m` M2648 improved/regressed 8/0 and M2655 improved/regressed 8/0; M2655 gates pass True
- `stable_aes` target metric `minimum_road_margin_m` M2648 improved/regressed 8/0 and M2655 improved/regressed 8/0; M2655 gates pass True
- `drift_required_recovery` target metric `drift_tradeoff_proxy` M2648 improved/regressed 8/0 and M2655 improved/regressed 8/0; M2655 gates pass True
- `unavoidable_mitigation` protected metric `severity_proxy` M2648 improved/regressed 7/1 and M2655 improved/regressed 7/1; M2655 gates pass False

## Report Gates

- `source_artifacts_present`: True
- `scenario_role_traceability`: True
- `target_protected_split_explicit`: True
- `m2655_negative_result_preserved`: True
- `actor_contract_p0_72_3_preserved`: True
- `no_hidden_or_oracle_actor_input`: True
- `no_ranking_promotion_success_rate_claims`: True
- `follow_up_manifest_registered`: True
