# M2810 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Offtrack-Containment Localization Panel Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel_materialization_pass`
- summary: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/summary.json`
- failure localization rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/failure_localization_rows.csv`
- outcome bucket rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/outcome_bucket_rows.csv`
- offtrack containment rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/offtrack_containment_rows.csv`
- stress-axis context rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/stress_axis_context_rows.csv`
- source-edge context rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/source_edge_context_rows.csv`
- guardrail context rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/guardrail_context_rows.csv`
- actor contract guard rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/actor_contract_guard_rows.csv`
- claim boundary rows: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/claim_boundary_rows.csv`
- gate matrix: `runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2811-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-localization-panel-materialization-result-audit.json`
- next: `m2811-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-localization-panel-materialization-result-audit`

## Localized Diagnostic Rows

- execution rows localized: 12
- diagnostic success rows: 2
- collision rows: 0
- offtrack rows: 10
- success obstacle-pass rows: 2
- collision negative-clearance rows: 0
- offtrack positive-clearance rows: 10
- offtrack containment rows: 10
- outcome bucket rows: 2

## Context And Guardrails

- stress-axis context rows: 4
- source-edge context rows: 8
- prior-surface guardrail rows: 37
- blocker guardrail rows: 7
- guardrails not executed: `true`
- protected rows in success denominator: `false`

## Actor Boundary

- actor contract P0 72/action 3: `true`
- hidden/oracle actor input detected: `false`
- localization, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`

## Claim Boundary

M2810 is no-rollout offtrack-containment localization from existing artifacts only. It performs no reset, step, policy action, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.

It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.
