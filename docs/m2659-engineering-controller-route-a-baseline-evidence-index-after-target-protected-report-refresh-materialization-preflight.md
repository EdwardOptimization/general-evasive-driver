# M2659 Route A Baseline Evidence Index After Target/Protected Report Refresh

- status: completed
- result_class: `engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh_pass`
- manifest: `experiments/manifests/m2659-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-preflight.json`
- summary: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/summary.json`
- evidence index: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/evidence_index.csv`
- gap matrix: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/gap_matrix.csv`
- claim boundary rows: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/claim_boundary_rows.csv`
- next-action admission: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/next_action_admission.csv`
- evidence rows: 12
- gap rows: 6
- claim rows: 16
- next-action rows: 5
- M2657 report indexed: True
- M2658 audit indexed: True
- target/protected split preserved: True
- protected failure blocking: True
- failed protected gates: `severity_proxy_non_regression;obstacle_penetration_non_regression;minimum_obstacle_clearance_preservation`
- selected M2655 candidate: `m2655_softened_gap_bias` diagnostic only, not winner
- selected next action: `m2660_route_a_baseline_evidence_index_refresh_result_audit`
- actor/action boundary: P0 observation 72 action 3; no hidden/oracle actor input
- supported operational claim: refreshed Route A baseline evidence index includes M2657/M2658
- rejected claims: repair success, driver performance, controller ranking, winner selection, checkpoint promotion, success-rate verdict, validation result, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation result, full ideal driver completion, or self-ID evidence
- follow-up manifest: `experiments/manifests/m2660-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-result-audit.json`
- next: `m2660-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-result-audit`

## Evidence Index

- m2639_previous_route_a_evidence_index: stale_but_traceable rows=7 role=mixed protected_blocking=False
- m2641_source_only_fresh_generalization_panel: materialized rows=160 role=mixed protected_blocking=False
- m2644_behavior_gap_taxonomy: materialized rows=4 role=target_and_protected protected_blocking=True
- m2648_gap_targeted_repair_evidence: materialized_not_promoted rows=7 role=target_and_protected protected_blocking=True
- m2655_mitigation_preserving_repair_evidence: materialized_not_promoted rows=9 role=target_and_protected protected_blocking=True
- m2656_repair_branch_pivot_synthesis: materialized rows=1 role=protected_blocker protected_blocking=True
- m2657_target_protected_report_summary: materialized rows=4 role=target_and_protected protected_blocking=True
- m2657_scenario_role_metric_report: materialized rows=4 role=target_and_protected protected_blocking=True
- m2657_target_tradeoff_rows: materialized_not_success_denominator rows=4 role=target protected_blocking=False
- m2657_protected_tradeoff_rows: materialized_blocking rows=5 role=protected protected_blocking=True
- m2657_protected_regression_focus_rows: materialized_blocking rows=8 role=protected protected_blocking=True
- m2658_target_protected_report_result_audit: materialized rows=1 role=target_and_protected protected_blocking=True

## Gap Matrix

- route_a_pre_m2657_index_staleness: resolved_by_m2659_materialization -> admitted_to_result_audit
- route_a_target_improvement_evidence: indexed_bounded -> admitted_to_index_only
- route_a_protected_mitigation_blocker: blocking -> blocks_repair_success_and_promotion
- route_a_same_row_repair_loop: closed_pending_new_evidence_axis -> not_admitted
- route_a_training_or_repair_admission: not_admitted -> not_admitted
- paper_self_id_verdict: not_supported -> not_admitted

## Claim Boundary

- baseline_evidence_index_refreshed: allowed=True pass=True
- target_protected_report_indexed: allowed=True pass=True
- protected_failure_blocker_indexed: allowed=True pass=True
- follow_up_result_audit_registered: allowed=True pass=True
- repair_success: allowed=False pass=True
- controller_family_ranking: allowed=False pass=True
- winner_selection: allowed=False pass=True
- checkpoint_promotion: allowed=False pass=True
- success_rate_verdict: allowed=False pass=True
- driver_performance: allowed=False pass=True
- validation_result: allowed=False pass=True
- high_fidelity_validation_result: allowed=False pass=True
- paper_level_evidence: allowed=False pass=True
- finite_window_vs_gru: allowed=False pass=True
- current_sim_verdict: allowed=False pass=True
- level3_self_identification: allowed=False pass=True

## Next Actions

- m2660_route_a_baseline_evidence_index_refresh_result_audit: admitted (M2659 materializes refreshed index and must be audited before another route decision)
- route_a_branch_synthesis_or_new_evidence_route: defer_until_m2660_audit (synthesis or new evidence route must consume the audited refreshed index)
- another_same_row_source_only_repair: not_admitted (M2656 closed the same-row repair loop and M2659 only refreshes the index)
- checkpoint_promotion_or_winner_selection: not_admitted (M2655 selected candidate is diagnostic trace only and protected gates fail)
- validation_success_rate_or_driver_performance_claim: not_admitted (M2659 is an evidence index refresh and performs no validation)
